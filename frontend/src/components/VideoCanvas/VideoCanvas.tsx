import React, { useEffect, useRef, useState } from 'react';
import { Box, Paper, IconButton, Stack, Tooltip, Typography, Button, Divider, TextField, Dialog, DialogTitle, DialogContent, DialogActions, Chip } from '@mui/material';
import { 
  Square, 
  Polyline,
  Delete, 
  Save, 
  Mouse,
  CheckCircle,
  Cancel
} from '@mui/icons-material';
import { fabric } from 'fabric';
import { getBackendBaseUrl } from '../../services/dataService';

interface VideoCanvasProps {
  onChange?: (roi: any) => void;
  initialRois?: any[];
  mode: 'view' | 'add' | 'edit';
  focusedRoiId?: string | null;
  cameraId?: string;
}

const VideoCanvas: React.FC<VideoCanvasProps> = ({ onChange, initialRois, mode, focusedRoiId, cameraId }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricCanvas = useRef<fabric.Canvas | null>(null);
  const [activeTool, setActiveTool] = useState<'select' | 'rect' | 'poly'>('select');
  
  const modeRef = useRef(mode);
  const activeToolRef = useRef(activeTool);
  const onChangeRef = useRef(onChange);

  useEffect(() => { modeRef.current = mode; }, [mode]);
  useEffect(() => { activeToolRef.current = activeTool; }, [activeTool]);
  useEffect(() => { onChangeRef.current = onChange; }, [onChange]);
  
  const points = useRef<{ x: number, y: number }[]>([]);
  const activeLine = useRef<fabric.Line | null>(null);

  useEffect(() => {
    if (canvasRef.current && !fabricCanvas.current) {
      fabricCanvas.current = new fabric.Canvas(canvasRef.current, {
        width: 800,
        height: 450,
        backgroundColor: '#000',
        selection: true
      });

      fabricCanvas.current.on('mouse:down', (opt) => {
        if (modeRef.current === 'view' || activeToolRef.current !== 'poly') return;
        const pointer = fabricCanvas.current?.getPointer(opt.e);
        if (!pointer) return;

        if (points.current.length > 2) {
          const first = points.current[0];
          const dist = Math.sqrt(Math.pow(pointer.x - first.x, 2) + Math.pow(pointer.y - first.y, 2));
          if (dist < 20) { finishPolygon(); return; }
        }

        points.current.push({ x: pointer.x, y: pointer.y });
        const circle = new fabric.Circle({ radius: 3, fill: '#2C3E50', left: pointer.x - 3, top: pointer.y - 3, selectable: false, name: 'temp' });
        fabricCanvas.current?.add(circle);

        if (points.current.length > 1) {
          const line = new fabric.Line([points.current[points.current.length - 2].x, points.current[points.current.length - 2].y, points.current[points.current.length - 1].x, points.current[points.current.length - 1].y], {
            stroke: '#2C3E50', strokeWidth: 1.5, selectable: false, name: 'temp'
          });
          fabricCanvas.current?.add(line);
        }
      });

      fabricCanvas.current.on('mouse:move', (opt) => {
        if (modeRef.current === 'view' || activeToolRef.current !== 'poly' || points.current.length === 0) return;
        const pointer = fabricCanvas.current?.getPointer(opt.e);
        if (!pointer) return;
        if (activeLine.current) fabricCanvas.current?.remove(activeLine.current);
        const last = points.current[points.current.length - 1];
        activeLine.current = new fabric.Line([last.x, last.y, pointer.x, pointer.y], { stroke: 'rgba(44, 62, 80, 0.4)', strokeWidth: 1.5, selectable: false });
        fabricCanvas.current?.add(activeLine.current);
        fabricCanvas.current?.renderAll();
      });

      fabricCanvas.current.on('object:modified', (e) => {
        const active = e.target;
        if (active && onChangeRef.current) {
          onChangeRef.current({
            type: active.type === 'polygon' ? 'polygon' : 'rect',
            coords: { left: active.left, top: active.top, width: active.width * (active.scaleX || 1), height: active.height * (active.scaleY || 1) },
            points: (active as any).points,
            color: active.stroke
          });
        }
      });

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Delete' || e.key === 'Backspace') {
          const activeElem = document.activeElement;
          if (activeElem && (activeElem.tagName === 'INPUT' || activeElem.tagName === 'TEXTAREA')) return;
          const activeObjects = fabricCanvas.current?.getActiveObjects();
          if (activeObjects && activeObjects.length > 0) {
            activeObjects.forEach(obj => fabricCanvas.current?.remove(obj));
            fabricCanvas.current?.discardActiveObject();
            fabricCanvas.current?.renderAll();
            if (onChangeRef.current) onChangeRef.current(null);
          }
        }
      };
      window.addEventListener('keydown', handleKeyDown);

      return () => { 
        fabricCanvas.current?.dispose(); 
        fabricCanvas.current = null;
        window.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, []);

  useEffect(() => {
    if (fabricCanvas.current) {
      const objects = fabricCanvas.current.getObjects();
      for (let i = objects.length - 1; i >= 0; i--) {
        fabricCanvas.current.remove(objects[i]);
      }
      fabricCanvas.current.setBackgroundColor('#000', fabricCanvas.current.renderAll.bind(fabricCanvas.current));
      
      const text = new fabric.Text('CAMERA_SOURCE_LIVE', {
        left: 310, top: 215, fontSize: 14, fill: '#333', selectable: false, fontFamily: 'monospace'
      });
      fabricCanvas.current.add(text);

      if (mode === 'view') {
        initialRois?.forEach(roi => {
          if (roi.coords) addShapeToCanvas(roi, false);
        });
      } else if (mode === 'add') {
        initialRois?.forEach(roi => {
          if (roi.coords) addShapeToCanvas(roi, false);
        });
      } else if (mode === 'edit') {
        initialRois?.forEach(roi => {
          if (roi.coords) {
            const isEditable = roi.id === focusedRoiId;
            addShapeToCanvas(roi, isEditable);
          }
        });
      }
      fabricCanvas.current.renderAll();
    }
  }, [mode, focusedRoiId, initialRois]);

  useEffect(() => {
    if (!fabricCanvas.current || !cameraId) return;

    const imgElement = document.createElement('img');
    imgElement.src = `${getBackendBaseUrl()}/api/v1/cameras/${cameraId}/stream`;
    imgElement.crossOrigin = 'anonymous';
    
    let animationId: number;
    
    imgElement.onload = () => {
      if (!fabricCanvas.current) return;
      const fabricImg = new fabric.Image(imgElement, {
        scaleX: 800 / (imgElement.width || 800),
        scaleY: 450 / (imgElement.height || 450),
        selectable: false,
        evented: false
      });
      fabricCanvas.current.setBackgroundImage(fabricImg, fabricCanvas.current.renderAll.bind(fabricCanvas.current));
      
      const renderLoop = () => {
        if (fabricCanvas.current) {
          fabricCanvas.current.renderAll();
          animationId = requestAnimationFrame(renderLoop);
        }
      };
      renderLoop();
    };

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [cameraId]);

  // The handlers are now inside the useEffect to avoid stale closures, so we don't need these separate functions.

  const finishPolygon = () => {
    const poly = new fabric.Polygon(points.current, { fill: 'rgba(44, 62, 80, 0.2)', stroke: '#2C3E50', strokeWidth: 2 });
    fabricCanvas.current?.add(poly);
    fabricCanvas.current?.setActiveObject(poly);
    fabricCanvas.current?.renderAll();
    
    const roiData = { coords: { left: poly.left, top: poly.top, width: poly.width, height: poly.height }, type: 'polygon', points: points.current, color: '#2C3E50' };
    if (onChangeRef.current) onChangeRef.current(roiData);
    
    points.current = [];
    const temps = fabricCanvas.current?.getObjects().filter(obj => obj.name === 'temp');
    temps?.forEach(t => fabricCanvas.current?.remove(t));
    if (activeLine.current) fabricCanvas.current?.remove(activeLine.current);
    setActiveTool('select');
  };

  const addRect = () => {
    setActiveTool('select');
    const rect = new fabric.Rect({
      left: 150, top: 150, width: 150, height: 100, fill: 'rgba(44, 62, 80, 0.2)', stroke: '#2C3E50', strokeWidth: 2,
      selectable: true, evented: true
    });
    fabricCanvas.current?.add(rect);
    fabricCanvas.current?.setActiveObject(rect);
    fabricCanvas.current?.renderAll();
    
    const roiData = { coords: { left: rect.left, top: rect.top, width: rect.width, height: rect.height }, type: 'rect', color: '#2C3E50' };
    if (onChangeRef.current) onChangeRef.current(roiData);
  };

  const handleDeleteSelected = () => {
    const activeObjects = fabricCanvas.current?.getActiveObjects();
    if (activeObjects && activeObjects.length > 0) {
      activeObjects.forEach(obj => {
        fabricCanvas.current?.remove(obj);
      });
      fabricCanvas.current?.discardActiveObject();
      fabricCanvas.current?.renderAll();
      if (onChangeRef.current) onChangeRef.current(null); // Clear active roi
    }
  };

  const addShapeToCanvas = (roi: any, isEditable: boolean) => {
    let shape;
    if (roi.type === 'polygon' && roi.points) {
      shape = new fabric.Polygon(roi.points, {
        left: roi.coords.left, top: roi.coords.top, fill: roi.color + '22', stroke: roi.color, strokeWidth: isEditable ? 3 : 2,
        selectable: isEditable, evented: isEditable, data: { id: roi.id, type: 'polygon' }
      });
    } else {
      shape = new fabric.Rect({
        left: roi.coords.left, top: roi.coords.top, width: roi.coords.width, height: roi.coords.height, fill: roi.color + '22', stroke: roi.color, strokeWidth: isEditable ? 3 : 2,
        selectable: isEditable, evented: isEditable, data: { id: roi.id, type: 'rect' }
      });
    }
    fabricCanvas.current?.add(shape);
    if (isEditable) fabricCanvas.current?.setActiveObject(shape);
  };

  return (
    <Box sx={{ bgcolor: '#FFFFFF', borderRadius: 0.5 }}>
      <Stack direction="row" spacing={1} sx={{ p: 1, bgcolor: '#f1f3f4', borderBottom: '1px solid #ddd' }}>
        {mode === 'view' ? (
          <Typography variant="caption" sx={{ alignSelf: 'center', ml: 1, fontWeight: 500, color: 'text.secondary' }}>PREVIEW MODE: ALL REGIONS VISIBLE</Typography>
        ) : (
          <>
            <Tooltip title="Navigation Tool"><IconButton onClick={() => setActiveTool('select')} size="small" color={activeTool === 'select' ? 'primary' : 'inherit'} sx={{ borderRadius: 1 }}><Mouse sx={{ fontSize: 18 }} /></IconButton></Tooltip>
            {mode !== 'view' && (
              <>
                <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
                <Tooltip title="Add Rectangle"><IconButton onClick={addRect} size="small" color={activeTool === 'rect' ? 'primary' : 'inherit'} sx={{ borderRadius: 1 }}><Square sx={{ fontSize: 18 }} /></IconButton></Tooltip>
                <Tooltip title="Polyline Tool"><IconButton onClick={() => setActiveTool('poly')} size="small" color={activeTool === 'poly' ? 'primary' : 'inherit'} sx={{ borderRadius: 1 }}><Polyline sx={{ fontSize: 18 }} /></IconButton></Tooltip>
                <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
                <Tooltip title="Delete Selected Shape"><IconButton onClick={handleDeleteSelected} size="small" color="error" sx={{ borderRadius: 1 }}><Delete sx={{ fontSize: 18 }} /></IconButton></Tooltip>
              </>
            )}
          </>
        )}
        <Box sx={{ flexGrow: 1 }} />
      </Stack>
      <Box sx={{ position: 'relative', bgcolor: '#000', display: 'flex', justifyContent: 'center', border: '1px solid #ddd' }}>
        <canvas ref={canvasRef} />
        {mode !== 'view' && (
          <Box sx={{ position: 'absolute', top: 8, right: 8 }}>
            <Chip 
              label={`${mode.toUpperCase()} MODE`} 
              size="small" 
              sx={{ 
                bgcolor: '#2C3E50', 
                color: 'white', 
                fontSize: '9px', 
                fontWeight: 'bold',
                height: 20,
                borderRadius: 0.5
              }} 
            />
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default VideoCanvas;
