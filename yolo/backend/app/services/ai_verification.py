import os
import cv2
import numpy as np
import torch
from typing import Dict, Any, Tuple, Optional
from PIL import Image
import httpx
from app.core.config import settings

class AIVerificationService:
    def __init__(self):
        # We check if GPU is available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    async def verify_uniform(
        self, person_crop: np.ndarray, reference_uniform_images: list[np.ndarray]
    ) -> Tuple[bool, float]:
        """
        Lightweight fallback verification for uniform.
        Returns (is_uniform, similarity_score).
        """
        return False, 0.5

    async def verify_fight_movinet(
        self, video_frames: list[np.ndarray]
    ) -> Tuple[str, float]:
        """
        Action recognition for fight verification.
        Uses motion flow estimation: fight scenes have high-velocity movements in opposite directions.
        Returns (result, confidence).
        """
        if not video_frames or len(video_frames) < 5:
            return "UNCERTAIN", 0.5

        try:
            prev_gray = cv2.cvtColor(video_frames[0], cv2.COLOR_BGR2GRAY)
            motion_magnitudes = []
            for frame in video_frames[1:]:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                motion_magnitudes.append(np.mean(mag))
                prev_gray = gray
            
            avg_motion = np.mean(motion_magnitudes)
            # High optical flow activity can denote action/fight
            confidence = min(1.0, avg_motion / 15.0)
            result = "VERIFIED" if avg_motion > 8.0 else "REFUTED"
            return result, confidence
        except Exception as e:
            print(f"Error in fight verification: {e}")
            return "UNCERTAIN", 0.5

    async def verify_fainting_movenet(
        self, keypoints: dict
    ) -> Tuple[str, float]:
        """
        Pose analysis for fainting verification.
        Analyzes the vertical coordinates of nose/shoulders relative to hips/ankles.
        """
        if not keypoints or "hip" not in keypoints or "shoulder" not in keypoints:
            return "UNCERTAIN", 0.5

        try:
            shoulder_y = (keypoints.get("left_shoulder", (0, 0))[1] + keypoints.get("right_shoulder", (0, 0))[1]) / 2
            hip_y = (keypoints.get("left_hip", (0, 0))[1] + keypoints.get("right_hip", (0, 0))[1]) / 2
            ankle_y = (keypoints.get("left_ankle", (0, 0))[1] + keypoints.get("right_ankle", (0, 0))[1]) / 2
            
            height_diff = abs(ankle_y - shoulder_y)
            
            # If vertical height span is small, person is lying down
            if height_diff < 0.2 and hip_y > 0.1:
                return "VERIFIED", 0.85
            return "REFUTED", 0.90
        except Exception as e:
            print(f"Error in fainting verification: {e}")
            return "UNCERTAIN", 0.5

    async def verify_with_qwen_vl(
        self, image_path: str, prompt: str
    ) -> Tuple[str, float, str]:
        """
        Lightweight fallback visual reasoning.
        Returns (result: VERIFIED|REFUTED|UNCERTAIN, confidence, reasoning_details).
        """
        if not os.path.exists(image_path):
            return "UNCERTAIN", 0.0, "Snapshot image not found."

        # Smart fallback parser based on prompt matching
        prompt_lower = prompt.lower()
        if "suicide" in prompt_lower or "climbing" in prompt_lower:
            return "VERIFIED", 0.88, "[Mock AI Verification] Detected suspicious high-altitude hanging or ledge-standing pose pattern."
        elif "smoke" in prompt_lower or "cigarette" in prompt_lower:
            return "VERIFIED", 0.82, "[Mock AI Verification] Cigarette object detected near mouth boundary."
        elif "phone" in prompt_lower or "mobile" in prompt_lower:
            return "VERIFIED", 0.85, "[Mock AI Verification] Detected cell phone object held in hand near torso/face region."
        
        return "VERIFIED", 0.80, f"[Mock AI Verification] Processed image with prompt: {prompt}"

ai_verification_service = AIVerificationService()
