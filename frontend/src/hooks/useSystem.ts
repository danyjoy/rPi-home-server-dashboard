import { useQuery } from "@tanstack/react-query";
import { api, type SystemResponse } from "../api/client";

const POLL_MS = 2500;

export function useSystem() {
  return useQuery<SystemResponse>({
    queryKey: ["system"],
    queryFn: api.getSystem,
    refetchInterval: POLL_MS,
    refetchIntervalInBackground: true,
    placeholderData: (prev) => prev,
  });
}
