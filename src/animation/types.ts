/** One exported clip (tools/animation/export_3d.py). Coordinates are mm, three.js axes. */
export type ClipBell = { c: number[]; h: number[][]; r: number; horns?: number[][] };

export type Clip = {
  id: string;
  duration: number;
  joints: string[];
  view: { azimuth: number; elevation: number };
  contract?: { variant?: string; counting?: string; phases?: string; contacts?: string };
  frames: { j: number[]; b: ClipBell[] }[];
};

export type Vec3 = [number, number, number];

/** A sampled pose in metres. */
export type Pose = {
  joints: Record<string, Vec3>;
  bells: { center: Vec3; handle: [Vec3, Vec3]; radius: number; horns?: [Vec3, Vec3] }[];
};
