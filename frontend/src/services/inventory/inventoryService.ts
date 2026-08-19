import { mockRequest } from "../api/client";
import { bloodStock, bloodUnits } from "../mock/data";

export const inventoryService = {
  getStock: () => mockRequest(bloodStock),
  listUnits: () => mockRequest(bloodUnits),
  getLowStock: () => mockRequest(bloodStock.filter((s) => s.units < s.threshold)),
};