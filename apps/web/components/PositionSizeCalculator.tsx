"use client";

import { useMemo, useState } from "react";

export function PositionSizeCalculator() {
  const [balance, setBalance] = useState(10000);
  const [riskPercent, setRiskPercent] = useState(1);
  const [entry, setEntry] = useState(1.085);
  const [stopLoss, setStopLoss] = useState(1.082);
  const [pipValuePerLot, setPipValuePerLot] = useState(10); // standard lot, most USD-quoted pairs

  const result = useMemo(() => {
    const riskAmount = balance * (riskPercent / 100);
    const stopDistancePips = Math.abs(entry - stopLoss) * 10000;
    if (stopDistancePips === 0 || pipValuePerLot === 0) return null;
    const lots = riskAmount / (stopDistancePips * pipValuePerLot);
    return { riskAmount, stopDistancePips, lots };
  }, [balance, riskPercent, entry, stopLoss, pipValuePerLot]);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-medium text-ink">Position size calculator</h1>
      <p className="text-sm text-ink/50">
        Pure arithmetic (Section 19 page 15) — nothing here is sent to the API; it&apos;s computed
        in your browser as you type.
      </p>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <section className="flex flex-col gap-4 rounded-lg border border-black/10 bg-panel p-5">
          {[
            { label: "Account balance ($)", value: balance, set: setBalance },
            { label: "Risk per trade (%)", value: riskPercent, set: setRiskPercent },
            { label: "Entry price", value: entry, set: setEntry },
            { label: "Stop loss price", value: stopLoss, set: setStopLoss },
            { label: "Pip value per standard lot ($)", value: pipValuePerLot, set: setPipValuePerLot },
          ].map(({ label, value, set }) => (
            <div key={label} className="flex flex-col gap-1">
              <label className="text-xs text-ink/50">{label}</label>
              <input
                type="number"
                value={value}
                onChange={(e) => set(Number(e.target.value))}
                step="any"
                className="tabular rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent"
              />
            </div>
          ))}
        </section>

        <section className="flex flex-col gap-4 rounded-lg border border-black/10 bg-panel p-5">
          <h2 className="text-sm font-medium text-ink/70">Result</h2>
          {!result ? (
            <p className="text-sm text-bearish">Entry and stop loss can&apos;t be equal.</p>
          ) : (
            <div className="tabular flex flex-col gap-3 text-sm text-ink">
              <div>
                <div className="text-ink/50">Risk amount</div>${result.riskAmount.toFixed(2)}
              </div>
              <div>
                <div className="text-ink/50">Stop distance</div>
                {result.stopDistancePips.toFixed(1)} pips
              </div>
              <div>
                <div className="text-ink/50">Position size</div>
                <span className="text-lg font-medium">{result.lots.toFixed(2)} lots</span>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
