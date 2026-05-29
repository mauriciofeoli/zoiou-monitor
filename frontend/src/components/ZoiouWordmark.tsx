interface WordmarkProps {
  size?: number;
  className?: string;
}

function ZEye({ size }: { size: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      aria-hidden="true"
      style={{ display: "block", flexShrink: 0 }}
    >
      <circle cx="50" cy="50" r="38" stroke="currentColor" strokeWidth="15" />
      <circle cx="50" cy="54" r="16" fill="currentColor" />
    </svg>
  );
}

export function ZoiouWordmark({ size = 24, className }: WordmarkProps) {
  const eyeSize = size * 0.62;
  const noseW = size * 0.115;
  const noseH = size * 0.46;

  return (
    <span
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        fontWeight: 800,
        letterSpacing: "-0.05em",
        lineHeight: 1,
        fontSize: size,
      }}
    >
      <span style={{ lineHeight: 0.7 }}>z</span>
      <ZEye size={eyeSize} />
      <span
        style={{
          width: noseW,
          height: noseH,
          borderRadius: 9999,
          background: "currentColor",
          display: "inline-block",
          flexShrink: 0,
          margin: `0 ${size * 0.02}px`,
          transform: "translateY(0.05em)",
        }}
      />
      <ZEye size={eyeSize} />
      <span style={{ lineHeight: 0.7, marginLeft: `-${size * 0.005}px` }}>u</span>
    </span>
  );
}

export function ZoiouEyeMark({ size = 40 }: { size?: number }) {
  const r = Math.round(size * 0.27);
  const eyeSize = size * 0.42;
  const noseW = size * 0.13;
  const noseH = size * 0.38;

  return (
    <span
      aria-hidden="true"
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: size,
        height: size,
        borderRadius: r,
        background: "var(--ink)",
        color: "var(--background)",
        flexShrink: 0,
      }}
    >
      <span style={{ display: "inline-flex", alignItems: "center", gap: size * 0.09 }}>
        <ZEye size={eyeSize} />
        <span
          style={{
            width: noseW,
            height: noseH,
            borderRadius: 9999,
            background: "currentColor",
            display: "inline-block",
            transform: "translateY(1px)",
          }}
        />
        <ZEye size={eyeSize} />
      </span>
    </span>
  );
}
