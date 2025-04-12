import { Automation } from "@/types/automations";
import { create } from "zustand";

interface AutomationsStore {
  automationsInContext: Automation[];
  setAutomationsInContext: (automations: Automation[]) => void;
}

export const useAutomationsStore = create<AutomationsStore>((set) => ({
  automationsInContext: [],
  setAutomationsInContext: (automations) => set(() => ({ automationsInContext: automations })),
})); 