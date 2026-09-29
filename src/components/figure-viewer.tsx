/* eslint-disable react/no-unknown-property -- react-three-fiber JSX props */
import { useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View, type GestureResponderEvent, type ViewStyle } from 'react-native';
import * as THREE from 'three';

import { clips } from '@/animation/clips';
import { Figure } from '@/animation/figure';
import { clipBounds, samplePose } from '@/animation/sample';
import { Canvas, useFrame, useThree } from '@/animation/three-canvas';
import { Palette, Radius } from '@/constants/theme';

type Orbit = { azimuth: number; elevation: number };

const FOV = 30;
const MIN_ELEVATION = -0.05;
const MAX_ELEVATION = 1.25;

function Scene({ clipId, orbit, speed, paused }: { clipId: string; orbit: React.RefObject<Orbit>; speed: number; paused: boolean }) {
  const clip = clips[clipId];
  const figure = useMemo(() => new Figure(), []);
  const bounds = useMemo(() => clipBounds(clip), [clip]);
  const { camera } = useThree();
  const time = useRef(0);

  useEffect(() => () => figure.dispose(), [figure]);

  useFrame((_, delta) => {
    if (!paused) time.current += Math.min(delta, 0.1);
    const { azimuth, elevation } = orbit.current;
    const target = new THREE.Vector3(...bounds.center);
    const distance = (bounds.size / 2 / Math.tan(THREE.MathUtils.degToRad(FOV / 2))) * 1.3;
    camera.position.set(
      target.x + distance * Math.sin(azimuth) * Math.cos(elevation),
      target.y + distance * Math.sin(elevation),
      target.z + distance * Math.cos(azimuth) * Math.cos(elevation),
    );
    camera.lookAt(target);
    figure.update(samplePose(clip, time.current, speed), camera.position);
  });

  return (
    <>
      <color attach="background" args={[Palette.stage]} />
      <ambientLight intensity={1.7} />
      <directionalLight position={[2, 4, 3]} intensity={1.6} />
      <directionalLight position={[-3, 2, -2]} intensity={0.5} />
      <primitive object={figure.group} />
    </>
  );
}

/**
 * Looping 3D exercise demonstration. Drag to spin around the figure and tilt
 * the view; the character keeps moving while you inspect it.
 */
export function FigureViewer({
  clipId,
  style,
  controls = true,
}: {
  clipId: string;
  style?: ViewStyle;
  controls?: boolean;
}) {
  const clip = clips[clipId];
  // Start from the watch camera, mirrored so the figure faces screen-right as on the watch.
  const home = useMemo<Orbit>(
    () => ({
      azimuth: -THREE.MathUtils.degToRad(clip.view.azimuth),
      elevation: THREE.MathUtils.degToRad(clip.view.elevation),
    }),
    [clip],
  );
  const orbit = useRef<Orbit>({ ...home });
  const start = useRef<Orbit>({ ...home });
  const [speed, setSpeed] = useState(1);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    orbit.current = { ...home };
  }, [home]);

  const touch = useRef({ x: 0, y: 0 });
  const onGrant = (e: GestureResponderEvent) => {
    touch.current = { x: e.nativeEvent.pageX, y: e.nativeEvent.pageY };
    start.current = { ...orbit.current };
  };
  const onMove = (e: GestureResponderEvent) => {
    const dx = e.nativeEvent.pageX - touch.current.x;
    const dy = e.nativeEvent.pageY - touch.current.y;
    orbit.current = {
      azimuth: start.current.azimuth - dx * 0.01,
      elevation: THREE.MathUtils.clamp(start.current.elevation + dy * 0.006, MIN_ELEVATION, MAX_ELEVATION),
    };
  };

  return (
    <View style={[styles.frame, style]}>
      <View
        style={StyleSheet.absoluteFill}
        onStartShouldSetResponder={() => true}
        onMoveShouldSetResponder={() => true}
        onResponderTerminationRequest={() => false}
        onResponderGrant={onGrant}
        onResponderMove={onMove}>
        <Canvas camera={{ fov: FOV, near: 0.05, far: 20 }} style={{ flex: 1 }}>
          <Scene clipId={clipId} orbit={orbit} speed={speed} paused={paused} />
        </Canvas>
      </View>
      {controls && (
        <View style={styles.controls} pointerEvents="box-none">
          <Chip label={paused ? 'Play' : 'Pause'} onPress={() => setPaused((p) => !p)} />
          <Chip label={speed === 1 ? '1×' : '½×'} onPress={() => setSpeed((s) => (s === 1 ? 0.5 : 1))} />
          <Chip label="Reset view" onPress={() => (orbit.current = { ...home })} />
        </View>
      )}
      {controls && (
        <Text style={styles.hint} pointerEvents="none">
          Drag to rotate
        </Text>
      )}
    </View>
  );
}

function Chip({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.chip, pressed && styles.chipPressed]}>
      <Text style={styles.chipText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  frame: { backgroundColor: Palette.stage, borderRadius: Radius.card, overflow: 'hidden', aspectRatio: 1 },
  controls: { position: 'absolute', bottom: 10, left: 10, right: 10, flexDirection: 'row', gap: 8 },
  chip: { backgroundColor: 'rgba(48,48,44,0.85)', paddingHorizontal: 12, paddingVertical: 7, borderRadius: 999 },
  chipPressed: { backgroundColor: Palette.pressed },
  chipText: { color: Palette.text, fontSize: 13, fontWeight: '600' },
  hint: { position: 'absolute', top: 10, right: 12, color: Palette.dim, fontSize: 12 },
});
