/**
 * Mirror local data to Supabase. Sessions are append-only and merged by id;
 * settings, bells and progression use last-write-wins on stateUpdatedAt.
 * Tables and row-level security: supabase/migrations/0001_init.sql.
 */
import type { SessionLog } from '@/core/session';
import { useApp, type RemoteState } from '@/store/app-store';

import { supabase } from './supabase';

export async function syncNow(): Promise<{ pushed: number; pulled: number } | null> {
  if (!supabase) return null;
  const { data: auth } = await supabase.auth.getSession();
  const userId = auth.session?.user.id;
  if (!userId) return null;

  const local = useApp.getState();
  const synced = new Set(local.syncedSessionIds);
  const pending = local.sessions.filter((s) => !synced.has(s.id));
  if (pending.length) {
    const { error } = await supabase
      .from('sessions')
      .upsert(pending.map((s) => ({ id: s.id, user_id: userId, started_at: s.startedAt, payload: s })));
    if (error) throw error;
  }

  const [sessions, state] = await Promise.all([
    supabase.from('sessions').select('payload').order('started_at', { ascending: false }),
    supabase.from('user_state').select('payload').maybeSingle(),
  ]);
  if (sessions.error) throw sessions.error;
  if (state.error) throw state.error;

  const remoteSessions = (sessions.data ?? []).map((row) => row.payload as SessionLog);
  const remoteState = state.data?.payload as RemoteState | undefined;
  local.mergeRemote({ sessions: remoteSessions, state: remoteState });
  local.markSynced(pending.map((s) => s.id));

  const after = useApp.getState();
  if (!remoteState || remoteState.stateUpdatedAt < after.stateUpdatedAt) {
    const payload: RemoteState = {
      settings: after.settings,
      prescriptions: after.prescriptions,
      customWorkouts: after.customWorkouts,
      stateUpdatedAt: after.stateUpdatedAt,
    };
    const { error } = await supabase.from('user_state').upsert({ user_id: userId, payload });
    if (error) throw error;
  }
  return { pushed: pending.length, pulled: remoteSessions.length };
}

/** Delete locally and, when signed in, remotely so it does not return on the next pull. */
export async function deleteSession(id: string) {
  useApp.getState().deleteSession(id);
  if (!supabase) return;
  const { data } = await supabase.auth.getSession();
  if (data.session) await supabase.from('sessions').delete().eq('id', id);
}
