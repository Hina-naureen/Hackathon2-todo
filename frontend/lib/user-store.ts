// lib/user-store.ts — simple file-based user store for Phase II (dev only)
// Users are persisted to .data/users.json on the Next.js server.
// Passwords are hashed with scrypt (Node.js built-in, no extra package needed).

import fs from 'fs/promises'
import path from 'path'
import crypto from 'crypto'
import { promisify } from 'util'

const scryptAsync = promisify(crypto.scrypt)

const DATA_DIR = path.join(process.cwd(), '.data')
const USERS_FILE = path.join(DATA_DIR, 'users.json')

interface StoredUser {
  id: string
  name: string
  email: string
  passwordHash: string
}

async function loadUsers(): Promise<StoredUser[]> {
  try {
    const data = await fs.readFile(USERS_FILE, 'utf-8')
    return JSON.parse(data) as StoredUser[]
  } catch {
    return []
  }
}

async function saveUsers(users: StoredUser[]): Promise<void> {
  await fs.mkdir(DATA_DIR, { recursive: true })
  await fs.writeFile(USERS_FILE, JSON.stringify(users, null, 2), 'utf-8')
}

async function hashPassword(password: string): Promise<string> {
  const salt = crypto.randomBytes(16).toString('hex')
  const derived = (await scryptAsync(password, salt, 64)) as Buffer
  return `${salt}:${derived.toString('hex')}`
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  const [salt, stored] = hash.split(':')
  if (!salt || !stored) return false
  const derived = (await scryptAsync(password, salt, 64)) as Buffer
  return crypto.timingSafeEqual(Buffer.from(stored, 'hex'), derived)
}

export async function findUserByEmail(email: string): Promise<StoredUser | null> {
  const users = await loadUsers()
  return users.find(u => u.email.toLowerCase() === email.toLowerCase()) ?? null
}

export async function createUser(data: {
  name: string
  email: string
  password: string
}): Promise<StoredUser> {
  const users = await loadUsers()
  const user: StoredUser = {
    id: crypto.randomUUID(),
    name: data.name,
    email: data.email,
    passwordHash: await hashPassword(data.password),
  }
  users.push(user)
  await saveUsers(users)
  return user
}
