import React from 'react'
import Main from '@/app/components/datasets/qa_documents'

export type IProps = {
  params: { datasetId: string }
}

const QADocuments = async ({
  params: { datasetId },
}: IProps) => {
  return (
    <Main datasetId={datasetId} />
  )
}

export default QADocuments
