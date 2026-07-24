import type { CustomerNextAction } from "../services/sessionIdentityAdapter";
import { CASE_STATUS_ROUTE, RECEIPT_ROUTE, TASK_HOME_ROUTE } from "./customerCaseSurface";
import { resolveHomeStartClaimUrl } from "./startClaimEntry";

/** Pure rendering map; the server owns the action selected for this context. */
export function routeForCustomerNextAction(nextAction: CustomerNextAction): string {
  switch (nextAction) {
    case "START_NEW_CLAIM":
      return resolveHomeStartClaimUrl();
    case "BROKER_REVIEW":
      return CASE_STATUS_ROUTE;
    case "CASE_CLOSED":
      return RECEIPT_ROUTE;
    case "CONTINUE_ACTIVE_CASE":
    case "UPLOAD_REQUEST_ITEM":
      return TASK_HOME_ROUTE;
    default:
      return "/pages/service-home/service-home";
  }
}
