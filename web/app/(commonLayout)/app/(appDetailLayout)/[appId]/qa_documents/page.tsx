import React from 'react'
import Main from '@/app/components/app/qa_documents'

export type IProps = {
  params: { appId: string }
}

const QADocuments = async ({
  params: { appId },
}: IProps) => {
  return (
    <Main appId={appId} />
  )
}

export default QADocuments
