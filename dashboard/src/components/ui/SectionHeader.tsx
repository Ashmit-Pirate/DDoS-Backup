export function SectionHeader({ 
  title, 
  eyebrow, 
  children 
}: { 
  title?: string, 
  eyebrow?: string, 
  children?: React.ReactNode 
}) {
  return (
    <div className="mb-10">
      {eyebrow && (
        <h2 className="text-[11px] font-bold tracking-widest text-[var(--muted-foreground)] font-sans uppercase mb-4">
          {eyebrow}
        </h2>
      )}
      {title && (
        <div className="text-2xl font-bold tracking-tight text-[var(--foreground)] font-sans">
          {title}
        </div>
      )}
      {children}
    </div>
  );
}
