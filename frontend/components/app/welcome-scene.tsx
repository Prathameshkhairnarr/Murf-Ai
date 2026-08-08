'use client';

import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, Line } from '@react-three/drei';
import * as THREE from 'three';

// ─── Disaster Management Radar Globe ───
function RadarGlobe() {
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame((state, delta) => {
    if (groupRef.current) {
      // Slow radar-like rotation
      groupRef.current.rotation.y += delta * 0.15;
      
      // Slight tilt tracking mouse for interactivity
      const pointerX = state.pointer.x * 0.1;
      const pointerY = state.pointer.y * 0.1;
      groupRef.current.rotation.x += (pointerY - groupRef.current.rotation.x) * 0.05;
      groupRef.current.rotation.z += (-pointerX - groupRef.current.rotation.z) * 0.05;
    }
  });

  return (
    <group ref={groupRef} rotation={[0.2, 0, 0]}>
      {/* Core wireframe sphere (The Earth / Grid) */}
      <Sphere args={[2, 32, 32]}>
        <meshBasicMaterial
          color="#ff3333"
          wireframe={true}
          transparent
          opacity={0.15}
          blending={THREE.AdditiveBlending}
        />
      </Sphere>

      {/* Inner solid sphere to give depth */}
      <Sphere args={[1.98, 32, 32]}>
        <meshBasicMaterial
          color="#110000"
          transparent
          opacity={0.8}
        />
      </Sphere>

      {/* Outer atmosphere glow */}
      <Sphere args={[2.1, 32, 32]}>
        <meshBasicMaterial
          color="#ff0000"
          transparent
          opacity={0.03}
          blending={THREE.AdditiveBlending}
          side={THREE.BackSide}
        />
      </Sphere>
      
      {/* Equator / Radar Ring */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[2.4, 2.42, 64]} />
        <meshBasicMaterial
          color="#ff4444"
          transparent
          opacity={0.4}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
    </group>
  );
}

export function WelcomeScene() {
  return (
    <div className="absolute inset-0 w-full h-full pointer-events-none opacity-80 mix-blend-screen">
      <Canvas camera={{ position: [0, 0, 5], fov: 60 }}>
        <RadarGlobe />
      </Canvas>
    </div>
  );
}
