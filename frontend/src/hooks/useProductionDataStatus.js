import { useEffect, useState } from 'react'
import { api } from '../api/client.js'

export function useProductionDataStatus(installationId) {
  const [state, setState] = useState({
    datasets: [],
    hasProductionData: false,
    isLoading: true,
  })

  useEffect(() => {
    if (!installationId) {
      setState({ datasets: [], hasProductionData: false, isLoading: false })
      return
    }

    let isMounted = true

    setState((current) => ({ ...current, isLoading: true }))
    api
      .listDatasets(installationId)
      .then((datasets) => {
        if (!isMounted) {
          return
        }

        setState({
          datasets,
          hasProductionData: datasets.length > 0,
          isLoading: false,
        })
      })
      .catch(() => {
        if (!isMounted) {
          return
        }

        setState({ datasets: [], hasProductionData: false, isLoading: false })
      })

    return () => {
      isMounted = false
    }
  }, [installationId])

  return state
}
