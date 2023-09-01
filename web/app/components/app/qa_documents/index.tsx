'use client'
import type { FC } from 'react'
import React, { useMemo, useState } from 'react'
import useSWR from 'swr'
import { useTranslation } from 'react-i18next'
import { useRouter } from 'next/navigation'
import { debounce, omit } from 'lodash-es'
import { PlusIcon } from '@heroicons/react/24/solid'
import List from './list'
import s from './style.module.css'
import Loading from '@/app/components/base/loading'
import Input from '@/app/components/base/input'
import Pagination from '@/app/components/base/pagination'
import { get } from '@/service/base'
import { fetchQADocuments } from '@/service/apps'
import Button from '@/app/components/base/button'
import AddQADocumentModal from '@/app/components/app/qa_documents/detail/index'
import { useAppContext } from '@/context/app-context'

// Custom page count is not currently supported.
const limit = 15

export const fetcher = (url: string) => get(url, {}, {})

type IDocumentsProps = {
  appId: string
}

const QADocuments: FC<IDocumentsProps> = ({ appId }) => {
  const { t } = useTranslation()
  const [searchValue, setSearchValue] = useState<string>('')
  const [currPage, setCurrPage] = React.useState<number>(0)
  const router = useRouter()
  const { isCurrentWorkspaceManager } = useAppContext()
  const [timerCanRun, setTimerCanRun] = useState(true)

  const query = useMemo(() => {
    return { page: currPage + 1, limit, keyword: searchValue }
  }, [searchValue, currPage])

  const { data: documentsRes, error, mutate } = useSWR(
    {
      action: 'fetchQADocuments',
      appId,
      params: query,
    },
    apiParams => fetchQADocuments(omit(apiParams, 'action')),
    { refreshInterval: 0 },
  )

  const total = documentsRes?.total || 0

  const [showAddQADocumentModal, setShowAddQADocumentModal] = React.useState(false)
  const handleOpenAddQADocumentModal = () => {
    setShowAddQADocumentModal(true)
  }

  const handleCloseAddQADocumentModal = () => {
    setShowAddQADocumentModal(false)
  }

  const resetList = () => {}

  const isLoading = !documentsRes && !error

  const documentsList = documentsRes?.data

  return (
    <div className='flex flex-col h-full overflow-y-auto'>
      <div className='flex flex-col justify-center gap-1 px-6 pt-4'>
        <h1 className={s.title}>{t('datasetQADocuments.list.title')}</h1>
        <p className={s.desc}>{t('datasetQADocuments.list.desc')}</p>
      </div>
      <div className='flex flex-col px-6 py-4 flex-1'>
        <div className='flex items-center justify-between'>
          <Input
            showPrefix
            wrapperClassName='!w-[200px]'
            className='!h-8 !text-[13px]'
            onChange={debounce(setSearchValue, 500)}
            value={searchValue}
          />
          {isCurrentWorkspaceManager && (
            <Button type='primary' onClick={handleOpenAddQADocumentModal} className='!h-8 !text-[13px]'>
              <PlusIcon className='h-4 w-4 mr-2 stroke-current' />
              {t('datasetQADocuments.list.add')}
            </Button>
          )}
        </div>
        {isLoading
          ? <Loading type='app' />
          : total > 0
            ? <List embeddingAvailable={isCurrentWorkspaceManager} documents={documentsList || []} appId={appId} onUpdate={mutate} />
            : 'No QA Documents'
        }
        {/* Show Pagination only if the total is more than the limit */}
        {(total && total > limit)
          ? <Pagination current={currPage} onChange={setCurrPage} total={total} limit={limit} />
          : null}
      </div>
      <AddQADocumentModal
        isShow={showAddQADocumentModal}
        onCancel={() => setShowAddQADocumentModal(false)}
        onSave={resetList}
      />
    </div>
  )
}

export default QADocuments
