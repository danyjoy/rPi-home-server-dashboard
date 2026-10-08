import { useQuery } from "@tanstack/react-query";
import { api, type StorageResponse } from "../api/client";

const POLL_MS = 5000;

export function useStorage() {
  return useQuery<StorageResponse>({
    queryKey: ["storage"],
    queryFn: api.getStorage,
    refetchInterval: POLL_MS,
    refetchIntervalInBackground: true,
    placeholderData: (prev) => prev,
  });
}
