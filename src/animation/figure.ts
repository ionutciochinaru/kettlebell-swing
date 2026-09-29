/**
 * The watch stick figure, built in 3D. Proportions, widths and colours follow
 * tools/animation/render.py: tapered limbs, the orange "dorito" shirt, pants
 * with cuffs, rounded shoes, a featureless head and a sloped kettlebell, all
 * with a thin black outline. As on the watch, the side nearer the camera is
 * drawn in ivory and the far side in grey; here that follows the orbit live.
 */
import * as THREE from 'three';
import { ConvexGeometry } from 'three/examples/jsm/geometries/ConvexGeometry.js';

import type { Pose, Vec3 } from './types';

export const FIGURE_COLORS = {
  ink: '#eeede4',
  far: '#8e9186',
  pants: '#bcc0ae',
  pantsFar: '#7f887a',
  cuff: '#7f887a',
  cuffFar: '#586152',
  accent: '#ff6b2b',
  bell: '#b4b1a6',
  prop: '#aaa99f',
  ground: '#191917',
  outline: '#000000',
};

const OUTLINE = 0.006;
const UP = new THREE.Vector3(0, 1, 0);
const SIDES = ['l', 'r'] as const;
type Side = (typeof SIDES)[number];

const v = (p: Vec3) => new THREE.Vector3(p[0], p[1], p[2]);
const mix = (a: THREE.Vector3, b: THREE.Vector3, t: number) => a.clone().lerp(b, t);

const outlineMaterial = new THREE.MeshBasicMaterial({ color: FIGURE_COLORS.outline, side: THREE.BackSide });
const lambert = (color: string) => new THREE.MeshLambertMaterial({ color });

/** A tapered tube through points: open cylinders with ball joints, plus an inverted-hull outline. */
class Chain {
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
class Solid {
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

/** Shoe profile from render.py, in a heel-origin frame: X across, Y up from sole, Z toward the toe. */
function shoeGeometry(length: number): THREE.BufferGeometry {
  const points: THREE.Vector3[] = [];
  const profile: [number, number, number][] = [
    [0, 0.025, 0.025], [0.1, 0.045, 0.039], [0.46, 0.05, 0.046],
    [0.76, 0.06, 0.032], [0.9, 0.051, 0.024], [0.98, 0.028, 0.015], [1, 0.004, 0.01],
  ];
  for (const [t, width, height] of profile) {
    for (const sign of [-1, 1]) {
      points.push(new THREE.Vector3(width * sign, 0, t * length), new THREE.Vector3(width * sign, height, t * length));
    }
  }
  // Instep: the ankle sits 0.075 m forward of the heel, 0.085 m above the sole.
  for (const sign of [-1, 1]) points.push(new THREE.Vector3(0.034 * sign, 0.012 + 0.07, 0.075));
  return new ConvexGeometry(points);
}

/** Sloped bell body from render.py, radius 1, axis +Y toward the handle. */
function bellGeometry(): THREE.BufferGeometry {
  const profile: [number, number][] = [
    [0, -0.99], [0.14, -0.99], [0.43, -0.9], [0.86, -0.5], [0.98, 0], [0.86, 0.4], [0.5, 0.64], [0, 0.7],
  ];
  return new THREE.LatheGeometry(profile.map(([x, y]) => new THREE.Vector2(x, y)), 28);
}

type SideParts = {
  leg: Chain;
  cuff: Chain;
  arm: Chain;
  hand: Chain;
  shoe: Solid;
  materials: { limb: THREE.MeshLambertMaterial; pants: THREE.MeshLambertMaterial; cuff: THREE.MeshLambertMaterial };
};

type BellParts = { body: Solid; handle: Chain; horns: Chain };

export class Figure {
  readonly group = new THREE.Group();
  private sides = {} as Record<Side, SideParts>;
  private waist: Chain;
  private neck: Chain;
  private head: Solid;
  private shirt: THREE.Mesh;
  private shirtOutline: THREE.Mesh;
  private bells: BellParts[] = [];
  private colors = {
    ink: new THREE.Color(FIGURE_COLORS.ink),
    far: new THREE.Color(FIGURE_COLORS.far),
    pants: new THREE.Color(FIGURE_COLORS.pants),
    pantsFar: new THREE.Color(FIGURE_COLORS.pantsFar),
    cuff: new THREE.Color(FIGURE_COLORS.cuff),
    cuffFar: new THREE.Color(FIGURE_COLORS.cuffFar),
  };

  constructor() {
    const ground = new THREE.Mesh(new THREE.CircleGeometry(0.95, 64), new THREE.MeshBasicMaterial({ color: FIGURE_COLORS.ground }));
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.002;
    this.group.add(ground);

    const pants = lambert(FIGURE_COLORS.pants);
    this.waist = new Chain(this.group, [0.07, 0.07], pants, false);
    for (const side of SIDES) {
      const materials = { limb: lambert(FIGURE_COLORS.ink), pants: lambert(FIGURE_COLORS.pants), cuff: lambert(FIGURE_COLORS.cuff) };
      this.sides[side] = {
        materials,
        leg: new Chain(this.group, [0.14, 0.146, 0.108, 0.079], materials.pants),
        cuff: new Chain(this.group, [0.088, 0.079], materials.cuff, false),
        // Strong upper arms taper through the elbow into slender forearms.
        arm: new Chain(this.group, [0.098, 0.12, 0.068, 0.038], materials.limb),
        hand: new Chain(this.group, [0.038, 0.046], materials.limb),
        shoe: new Solid(this.group, shoeGeometry(0.235), materials.limb, [1.18, 1.25, 1.06]),
      };
    }
    const ink = lambert(FIGURE_COLORS.ink);
    this.neck = new Chain(this.group, [0.048, 0.048], ink, false);
    this.head = new Solid(this.group, new THREE.SphereGeometry(1, 28, 20), ink, [1.07, 1.055, 1.065]);

    const shirtMaterial = lambert(FIGURE_COLORS.accent);
    this.shirt = new THREE.Mesh(new THREE.BufferGeometry(), shirtMaterial);
    this.shirtOutline = new THREE.Mesh(this.shirt.geometry, outlineMaterial);
    this.group.add(this.shirt, this.shirtOutline);

    for (let i = 0; i < 2; i++) {
      this.bells.push({
        body: new Solid(this.group, bellGeometry(), lambert(FIGURE_COLORS.bell), [1.07, 1.06, 1.07]),
        handle: new Chain(this.group, [0.024, 0.024, 0.024, 0.024], ink),
        horns: new Chain(this.group, [0.024, 0.024, 0.024, 0.024], lambert(FIGURE_COLORS.prop)),
      });
    }
  }

  /** Pose the figure. `camera` is the eye position, for near/far side shading. */
  update(pose: Pose, camera: THREE.Vector3) {
    const j = Object.fromEntries(Object.entries(pose.joints).map(([k, p]) => [k, v(p)])) as Record<string, THREE.Vector3>;
    const trunkUp = j.chest.clone().sub(j.pelvis).normalize();
    const sideways = j.shoulder_l.clone().sub(j.shoulder_r).normalize();
    const forward = new THREE.Vector3().crossVectors(sideways, trunkUp).normalize();
    const offset = (p: THREE.Vector3, side = 0, along = 0, front = 0) =>
      p.clone().addScaledVector(sideways, side).addScaledVector(trunkUp, along).addScaledVector(forward, front);

    // Near side ivory, far side grey, blended over ~10 cm of depth difference.
    const depth = (p: THREE.Vector3) => -p.distanceTo(camera);
    const nearness = depth(j.shoulder_l) + depth(j.hip_l) - depth(j.shoulder_r) - depth(j.hip_r);
    const leftNear = THREE.MathUtils.smoothstep(nearness, -0.1, 0.1);

    this.waist.update([offset(j.hip_l, 0, 0.012), offset(j.hip_r, 0, 0.012)]);
    for (const side of SIDES) {
      const parts = this.sides[side];
      const t = side === 'l' ? leftNear : 1 - leftNear;
      parts.materials.limb.color.lerpColors(this.colors.far, this.colors.ink, t);
      parts.materials.pants.color.lerpColors(this.colors.pantsFar, this.colors.pants, t);
      parts.materials.cuff.color.lerpColors(this.colors.cuffFar, this.colors.cuff, t);

      const [hip, knee, ankle] = [j[`hip_${side}`], j[`knee_${side}`], j[`ankle_${side}`]];
      const cuffEnd = mix(ankle, knee, 0.11);
      parts.leg.update([hip, mix(hip, knee, 0.38), knee, cuffEnd]);
      parts.cuff.update([mix(ankle, knee, 0.2), cuffEnd]);

      const [shoulder, elbow, wrist, palm] = [j[`shoulder_${side}`], j[`elbow_${side}`], j[`wrist_${side}`], j[`palm_${side}`]];
      parts.arm.update([shoulder, mix(shoulder, elbow, 0.43), elbow, wrist]);
      parts.hand.update([wrist, palm]);

      const heel = j[`heel_${side}`];
      const along = j[`toe_${side}`].clone().sub(heel).normalize();
      const normal = new THREE.Vector3().crossVectors(along, new THREE.Vector3(1, 0, 0)).normalize();
      const across = new THREE.Vector3().crossVectors(normal, along);
      parts.shoe.place(heel, across, normal, along);
    }

    this.updateShirt(j, offset);
    this.neck.update([mix(j.chest, j.neck, 0.66), mix(j.neck, j.head, 0.36)]);

    // Featureless head: taller than wide, facing the authored gaze.
    const headUp = j.head.clone().sub(j.neck).normalize();
    const headFront = j.face.clone().sub(j.head);
    headFront.addScaledVector(headUp, -headFront.dot(headUp)).normalize();
    const headSide = new THREE.Vector3().crossVectors(headUp, headFront);
    this.head.place(j.head.clone().addScaledVector(headFront, 0.004), headSide, headUp, headFront, [0.08, 0.108, 0.091]);

    this.bells.forEach((parts, i) => {
      const bell = pose.bells[i];
      parts.body.visible = !!bell;
      parts.handle.visible = !!bell && !bell.horns;
      parts.horns.visible = !!bell?.horns;
      if (!bell) return;
      const center = v(bell.center);
      const [h0, h1] = bell.handle.map(v);
      const axis = mix(h0, h1, 0.5).sub(center).normalize();
      const acrossRaw = h0.clone().sub(h1);
      const across = acrossRaw.addScaledVector(axis, -acrossRaw.dot(axis)).normalize();
      const depthAxis = new THREE.Vector3().crossVectors(across, axis);
      parts.body.place(center, across, axis, depthAxis, [bell.radius, bell.radius, bell.radius]);
      if (bell.horns) {
        const [a0, a1] = bell.horns.map(v);
        parts.horns.update([a0, h0, h1, a1]);
      } else {
        const attach = (sign: number) =>
          center.clone().addScaledVector(axis, 0.4 * bell.radius).addScaledVector(across, sign * 0.64 * bell.radius);
        parts.handle.update([attach(1), h0, h1, attach(-1)]);
      }
    });
  }

  private updateShirt(j: Record<string, THREE.Vector3>, offset: (p: THREE.Vector3, side?: number, along?: number, front?: number) => THREE.Vector3) {
    // Broad orange shoulders narrowing to the waist.
    const points: THREE.Vector3[] = [];
    for (const front of [-1, 1]) {
      points.push(
        offset(j.chest, 0.05, 0.08, 0.055 * front),
        offset(j.chest, -0.05, 0.08, 0.055 * front),
        offset(j.shoulder_l, -0.018, 0.01, 0.076 * front),
        offset(j.shoulder_r, 0.018, 0.01, 0.076 * front),
        offset(j.pelvis, 0.065, 0.02, 0.043 * front),
        offset(j.pelvis, -0.065, 0.02, 0.043 * front),
      );
    }
    const old = this.shirt.geometry;
    const geometry = new ConvexGeometry(points);
    this.shirt.geometry = geometry;
    this.shirtOutline.geometry = geometry;
    old.dispose();
    const centroid = points.reduce((sum, p) => sum.add(p), new THREE.Vector3()).divideScalar(points.length);
    this.shirtOutline.position.copy(centroid).multiplyScalar(1 - 1.06);
    this.shirtOutline.scale.setScalar(1.06);
  }

  dispose() {
    this.group.traverse((object) => {
      if (object instanceof THREE.Mesh) object.geometry.dispose();
    });
  }
}
