/** Selection, tab and focus state for the tradition page. Pure reducer. */

export type Tab = "bundle" | "texts";

export interface FocusRequest {
  keys: string[];
  seq: number;
}

export interface ExplorerState {
  tab: Tab;
  nodeKey: string | null;
  chainId: number | null;
  focus: FocusRequest | null;
}

export type ExplorerAction =
  | { type: "tab"; tab: Tab }
  | { type: "selectNode"; key: string; focus: boolean }
  | { type: "selectChain"; chainId: number; pathKeys: string[]; fallbackNodeKey: string | null; focus: boolean }
  | { type: "clear" };

export const initialExplorerState: ExplorerState = { tab: "bundle", nodeKey: null, chainId: null, focus: null };

function focusOn(state: ExplorerState, keys: string[]): FocusRequest {
  return { keys, seq: (state.focus?.seq ?? 0) + 1 };
}

export function explorerReducer(state: ExplorerState, action: ExplorerAction): ExplorerState {
  switch (action.type) {
    case "tab":
      return { ...state, tab: action.tab };
    case "selectNode":
      return {
        tab: "bundle",
        nodeKey: action.key,
        chainId: null,
        focus: action.focus ? focusOn(state, [action.key]) : state.focus,
      };
    case "selectChain":
      return {
        tab: "bundle",
        nodeKey: state.nodeKey ?? action.fallbackNodeKey,
        chainId: state.chainId === action.chainId && !action.focus ? null : action.chainId,
        focus: action.focus ? focusOn(state, action.pathKeys) : state.focus,
      };
    case "clear":
      return { ...state, nodeKey: null, chainId: null };
  }
}
