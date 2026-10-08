import { useQuery } from "@tanstack/react-query";
import { api, type NetworkResponse } from "../api/client";

const POLL_MS = 2500;

export function useNetwork() {
  return useQuery<NetworkResponse>({
    queryKey: ["network"],
    queryFn: api.getNetwork,
    refetchInterval: POLL_MS,
    refetchIntervalInBackground: true,
    placeholderData: (prev) => prev,
  });
}
