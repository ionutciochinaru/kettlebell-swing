/** Reusable figure pieces: tapered chains and rigid solids with inverted-hull outlines. */
import * as THREE from 'three';

import type { Vec3 } from './types';

export const OUTLINE = 0.006;
export const UP = new THREE.Vector3(0, 1, 0);
export const outlineMaterial = new THREE.MeshBasicMaterial({ color: '#000000', side: THREE.BackSide });
export const lambert = (color: string) => new THREE.MeshLambertMaterial({ color });

/** A tapered tube through points: open cylinders with ball joints, plus an inverted-hull outline. */
export class Chain {
  private segments: { mesh: THREE.Mesh; outline?: THREE.Mesh }[] = [];
  private balls: { mesh: THREE.Mesh; outline?: THREE.Mesh }[] = [];

  constructor(parent: THREE.Object3D, widths: number[], material: THREE.Material, outline = true) {
    const radii = widths.map((w) => w / 2);
    for (let i = 0; i < radii.length - 1; i++) {
      const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radii[i + 1], radii[i], 1, 18, 1, true), material);
      const shell = outline
        ? new THREE.Mesh(new THREE.CylinderGeometry(radii[i + 1] + OUTLINE, radii[i] + OUTLINE, 1, 18, 1, true), outlineMaterial)
        : undefined;
      this.segments.push({ mesh, outline: shell });
      parent.add(mesh);
      if (shell) parent.add(shell);
    }
    for (const r of radii) {
      const mesh = new THREE.Mesh(new THREE.SphereGeometry(r, 18, 12), material);
      const shell = outline ? new THREE.Mesh(new THREE.SphereGeometry(r + OUTLINE, 18, 12), outlineMaterial) : undefined;
      this.balls.push({ mesh, outline: shell });
      parent.add(mesh);
      if (shell) parent.add(shell);
    }
  }

  update(points: THREE.Vector3[]) {
    const direction = new THREE.Vector3();
    this.segments.forEach(({ mesh, outline }, i) => {
      const a = points[i];
      const b = points[i + 1];
      direction.subVectors(b, a);
      const length = Math.max(direction.length(), 1e-6);
      for (const m of outline ? [mesh, outline] : [mesh]) {
        m.position.copy(a).add(b).multiplyScalar(0.5);
        m.quaternion.setFromUnitVectors(UP, direction.clone().divideScalar(length));
        m.scale.set(1, length, 1);
      }
    });
    this.balls.forEach(({ mesh, outline }, i) => {
      mesh.position.copy(points[i]);
      outline?.position.copy(points[i]);
    });
  }

  set visible(value: boolean) {
    for (const part of [...this.segments, ...this.balls]) {
      part.mesh.visible = value;
      if (part.outline) part.outline.visible = value;
    }
  }
}

/** Rigid mesh placed each frame by an orthonormal basis; outline is a scaled back-face shell. */
export class Solid {
  readonly mesh: THREE.Mesh;
  readonly outline: THREE.Mesh;

  constructor(parent: THREE.Object3D, geometry: THREE.BufferGeometry, material: THREE.Material, outlineScale: Vec3) {
    this.mesh = new THREE.Mesh(geometry, material);
    this.outline = new THREE.Mesh(geometry, outlineMaterial);
    this.outline.userData.outlineScale = outlineScale;
    this.mesh.matrixAutoUpdate = false;
    this.outline.matrixAutoUpdate = false;
    parent.add(this.mesh, this.outline);
  }

  place(origin: THREE.Vector3, x: THREE.Vector3, y: THREE.Vector3, z: THREE.Vector3, scale: Vec3 = [1, 1, 1]) {
    const basis = new THREE.Matrix4().makeBasis(x, y, z).setPosition(origin);
    this.mesh.matrix.copy(basis).multiply(new THREE.Matrix4().makeScale(...scale));
    const [ox, oy, oz] = this.outline.userData.outlineScale as Vec3;
    this.outline.matrix.copy(basis).multiply(new THREE.Matrix4().makeScale(scale[0] * ox, scale[1] * oy, scale[2] * oz));
  }

  set visible(value: boolean) {
    this.mesh.visible = value;
    this.outline.visible = value;
  }
}

