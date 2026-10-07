export default function TodoPage({ phase, title }: { phase: number; title: string }) {
  return (
    <main style={{ padding: 32 }}>
      <h1>{title}</h1>
      <p>TODO phase {phase}: this page is a Phase 0 placeholder.</p>
    </main>
  );
}
