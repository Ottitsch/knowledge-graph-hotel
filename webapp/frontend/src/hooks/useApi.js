import useSWR from 'swr'

const fetcher = (url) =>
  fetch(url).then((res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  })

export function useApi(path) {
  const { data, error, isLoading } = useSWR(path, fetcher, {
    revalidateOnFocus: false,
  })
  return { data, error, isLoading }
}
