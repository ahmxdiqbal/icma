import { describe, expect, it } from "vitest";
import { explorerReducer, initialExplorerState, type ExplorerAction, type ExplorerState } from "./explorer-state";

const chain = (chainId: number, focus: boolean): ExplorerAction => ({
  type: "selectChain",
  chainId,
  pathKeys: ["prophet", "n:1", "n:5"],
  fallbackNodeKey: "n:5",
  focus,
});

describe("explorerReducer", () => {
  it("selects a node, clears any chain and returns to the graph", () => {
    const from: ExplorerState = { ...initialExplorerState, tab: "texts", chainId: 9 };
    const next = explorerReducer(from, { type: "selectNode", key: "n:2", focus: true });
    expect(next).toMatchObject({ tab: "bundle", nodeKey: "n:2", chainId: null });
    expect(next.focus).toEqual({ keys: ["n:2"], seq: 1 });
  });

  it("keeps the previous focus request when selecting from inside the graph", () => {
    const next = explorerReducer(initialExplorerState, { type: "selectNode", key: "n:2", focus: false });
    expect(next.focus).toBeNull();
  });

  it("falls back to the chain's collector when no node is selected", () => {
    const next = explorerReducer(initialExplorerState, chain(40, true));
    expect(next).toMatchObject({ nodeKey: "n:5", chainId: 40, tab: "bundle" });
    expect(next.focus?.keys).toEqual(["prophet", "n:1", "n:5"]);
  });

  it("toggles a chain off when it is selected again from the panel", () => {
    const on = explorerReducer({ ...initialExplorerState, nodeKey: "n:1" }, chain(40, false));
    expect(on.chainId).toBe(40);
    expect(explorerReducer(on, chain(40, false)).chainId).toBeNull();
  });

  it("increments the focus sequence so repeated requests re-fire", () => {
    const once = explorerReducer(initialExplorerState, chain(40, true));
    expect(explorerReducer(once, chain(40, true)).focus?.seq).toBe(2);
  });

  it("clears the selection but keeps the tab", () => {
    const from: ExplorerState = { tab: "bundle", nodeKey: "n:1", chainId: 3, focus: null };
    expect(explorerReducer(from, { type: "clear" })).toMatchObject({ nodeKey: null, chainId: null, tab: "bundle" });
  });
});
