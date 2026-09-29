import { Redirect } from 'expo-router';

/** OAuth returns here on native; the auth session has already captured the code. */
export default function AuthCallback() {
  return <Redirect href="/" />;
}
