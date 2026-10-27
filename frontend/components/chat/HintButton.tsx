type HintButtonProps = {
  onRequest: () => void;
  isRequesting: boolean;
  disabled?: boolean;
};

export function HintButton({ onRequest, isRequesting, disabled = false }: HintButtonProps) {
  return (
    <button className="secondary-button" type="button" disabled={disabled || isRequesting} onClick={onRequest}>
      {isRequesting ? "Getting hint…" : "💡 Get a hint"}
    </button>
  );
}
