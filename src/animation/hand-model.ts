/**
 * Stylised mitten hands. A gripping hand is a palm block plus a finger band
 * wrapped around the handle; a free hand is a relaxed fist that lies flat when
 * resting on the floor. Grip is detected from the pose (wrist on a handle).
 */
import * as THREE from 'three';

import { Solid } from './parts';

export type Grip = { point: THREE.Vector3; axis: THREE.Vector3 };

const WORLD_UP = new THREE.Vector3(0, 1, 0);

function perpendicular(v: THREE.Vector3): THREE.Vector3 {
  const trial = Math.abs(v.y) < 0.9 ? WORLD_UP : new THREE.Vector3(1, 0, 0);
  return new THREE.Vector3().crossVectors(v, trial).normalize();
}

export class HandModel {
  private palm: Solid;
  private fingers: Solid;

  constructor(parent: THREE.Object3D, material: THREE.Material) {
    this.palm = new Solid(parent, new THREE.SphereGeometry(1, 18, 12), material, [1.16, 1.1, 1.24]);
    // Three-quarter ring (tube radius 16 mm) that wraps the 17 mm handle.
    this.fingers = new Solid(parent, new THREE.TorusGeometry(0.032, 0.016, 10, 20, Math.PI * 1.5), material, [1.12, 1.12, 1.1]);
  }

  update(wrist: THREE.Vector3, palm: THREE.Vector3, grip?: Grip) {
    if (grip) {
      const axis = grip.axis.clone().normalize();
      // Palm side: from the handle toward the wrist, perpendicular to the handle.
      const p = wrist.clone().sub(grip.point);
      p.addScaledVector(axis, -p.dot(axis));
      if (p.lengthSq() < 1e-8) p.copy(perpendicular(axis));
      p.normalize();

      const knuckles = grip.point.clone().addScaledVector(p, 0.034);
      const along = knuckles.clone().sub(wrist);
      const length = Math.max(along.length(), 0.02);
      along.normalize();
      const across = axis.clone().addScaledVector(along, -axis.dot(along)).normalize();
      const thickness = new THREE.Vector3().crossVectors(across, along);
      this.palm.place(wrist.clone().lerp(knuckles, 0.5), across, along, thickness, [0.045, length / 2 + 0.016, 0.027]);

      // Ring opening faces the palm, so palm + fingers close around the bar.
      const q = new THREE.Vector3().crossVectors(axis, p);
      const x = p.clone().add(q).multiplyScalar(Math.SQRT1_2);
      const y = q.clone().sub(p).multiplyScalar(Math.SQRT1_2);
      this.fingers.place(grip.point, x, y, axis, [1, 1, 2.4]);
      this.fingers.visible = true;
      return;
    }
    const along = palm.clone().sub(wrist);
    if (along.lengthSq() < 1e-8) along.set(0, -1, 0);
    along.normalize();
    // Thickness axis as close to world-up as possible: flat on the floor, edge-on when hanging.
    const thickness = WORLD_UP.clone().addScaledVector(along, -WORLD_UP.dot(along));
    if (thickness.lengthSq() < 1e-6) thickness.copy(perpendicular(along));
    thickness.normalize();
    const across = new THREE.Vector3().crossVectors(along, thickness);
    this.palm.place(wrist.clone().addScaledVector(along, 0.045), across, along, thickness, [0.04, 0.052, 0.026]);
    this.fingers.visible = false;
  }
}
