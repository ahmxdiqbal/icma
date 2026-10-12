"use client";

import { createContext, useContext } from "react";
import type { TraditionIndex } from "@/lib/tradition-index";

export interface ExplorerActions {
  /** Select a node; `focus` also pans the graph to it (used from outside the graph). */
  selectNode: (key: string, focus?: boolean) => void;
  /** Toggle a chain's highlight; `focus` also fits the graph to the chain's path. */
  selectChain: (chainId: number, focus?: boolean) => void;
  clear: () => void;
}

export interface ExplorerContextValue {
  actions: ExplorerActions;
  index: TraditionIndex;
}

export const ExplorerContext = createContext<ExplorerContextValue | null>(null);

export function useExplorer(): ExplorerContextValue {
  const value = useContext(ExplorerContext);
  if (value === null) throw new Error("useExplorer must be used inside ExplorerContext");
  return value;
}
