import { EncryptJWT, jwtDecrypt } from "jose";

export async function encodeSessionCookie(value: unknown, secret: string): Promise<string> {
  const key = new TextEncoder().encode(secret);
  return new EncryptJWT({ value }).setProtectedHeader({ alg: "dir", enc: "A256GCM" }).setIssuedAt().setExpirationTime("2h").encrypt(key);
}

export async function decodeSessionCookie<T>(token: string, secret: string): Promise<T> {
  const key = new TextEncoder().encode(secret);
  const { payload } = await jwtDecrypt(token, key);
  return payload.value as T;
}
