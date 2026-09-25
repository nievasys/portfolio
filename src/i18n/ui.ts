export const languages = {
  es: "es",
  en: "en"
} as const;

export type Locale = keyof typeof languages;

export const defaultLocale: Locale = "es";

export const translations = {
  es: {
    nav: {
      ariaLabel: "Principal",
      cv: "cv",
      proyectos: "proyectos"
    },
    cv: "https://docs.google.com/document/d/1JZs3mGGqB8_AIYdcZRhXMkH-deenasCI/edit?usp=sharing&ouid=108187799550111208389&rtpof=true&sd=true",
    social: {
      github: "GitHub de nieva agustin",
      linkedin: "LinkedIn de nieva agustin"
    },
    about: {
      role: "desarrollador de software",
      currently: "actualmente construyendo",
      city: "buenos aires",
      country: "argentina"
    }
  },
  en: {
    nav: {
      ariaLabel: "Main",
      cv: "cv",
      proyectos: "projects"
    },
    cv: "https://docs.google.com/document/d/1281z3lMn0RtXUUQbqVy_FUfW18WJPXPI/edit?usp=sharing&ouid=108187799550111208389&rtpof=true&sd=true",
    social: {
      github: "GitHub of nieva agustin",
      linkedin: "LinkedIn of nieva agustin"
    },
    about: {
      role: "software developer",
      currently: "currently building",
      city: "buenos aires",
      country: "argentina"
    }
  }
} as const;

export type Translation = (typeof translations)[typeof defaultLocale];

export function useTranslations(locale: Locale): Translation {
  return translations[locale] ?? translations[defaultLocale];
}