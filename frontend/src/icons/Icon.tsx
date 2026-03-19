import styles from "./Icon.module.css";

export const ICONS = {
  clip: "/icons/clip.svg",
  "file-up": "/icons/file-up.svg",
  "file-plus": "/icons/file-plus.svg",
  "file-doc": "/icons/file-doc.svg",
  x: "/icons/x.svg",
  "triangle-alert": "/icons/triangle-alert.svg",
  "chart-column": "/icons/chart-column.svg",
  eye: "/icons/eye.svg",
} as const;

export type IconName = keyof typeof ICONS;

type IconProps = {
  name: IconName;
  size?: number;
  className?: string;
};

export function Icon({ name, size = 24, className }: IconProps) {
  const url = ICONS[name];
  return (
    <span
      className={`${styles.icon} ${className ?? ""}`}
      style={{
        width: size,
        height: size,
        maskImage: `url(${url})`,
        WebkitMaskImage: `url(${url})`,
      }}
      role="img"
      aria-hidden
    />
  );
}
