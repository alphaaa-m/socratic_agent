import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password.").max(128, "Password is too long."),
});

export const registerSchema = z.object({
  name: z.string().trim().min(1, "Enter your name.").max(120, "Name must be 120 characters or fewer."),
  email: z.string().trim().email("Enter a valid email address."),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters.")
    .max(128, "Password must be 128 characters or fewer.")
    .regex(/[A-Za-z]/, "Password must contain at least one letter.")
    .regex(/\d/, "Password must contain at least one number."),
});

export type LoginValues = z.infer<typeof loginSchema>;
export type RegisterValues = z.infer<typeof registerSchema>;
