'use client'
import type { FC, SVGProps } from 'react'
import React, { memo, useEffect, useMemo, useState } from 'react'
import { ArrowDownIcon, TrashIcon } from '@heroicons/react/24/outline'
import { ExclamationCircleIcon, HashtagIcon } from '@heroicons/react/24/solid'
import dayjs from 'dayjs'
import { useContext } from 'use-context-selector'
import { useRouter } from 'next/navigation'
import { useTranslation } from 'react-i18next'
import cn from 'classnames'
import s from './style.module.css'
import Switch from '@/app/components/base/switch'
import Popover from '@/app/components/base/popover'
import Modal from '@/app/components/base/modal'
import Button from '@/app/components/base/button'
import Tooltip from '@/app/components/base/tooltip'
import { ToastContext } from '@/app/components/base/toast'
import type { IndicatorProps } from '@/app/components/header/indicator'
import Indicator from '@/app/components/header/indicator'
import { asyncRunSafe } from '@/utils'
import { deleteQADocument, updateQADocument } from '@/service/datasets'
import { type QADocumentDetail, type QADocumentUpdator } from '@/models/datasets'
import type { CommonResponse } from '@/models/common'
import { DotsHorizontal, Edit03, HelpCircle, XClose } from '@/app/components/base/icons/src/vender/line/general'
import { useEventEmitterContextContext } from '@/context/event-emitter'
import AutoHeightTextarea from '@/app/components/base/auto-height-textarea/common'

export const QADocumentIndexTag: FC<{ positionId: string | number; className?: string }> = ({ positionId, className }) => {
  const localPositionId = useMemo(() => {
    const positionIdStr = String(positionId)
    if (positionIdStr.length >= 3)
      return positionId
    return positionIdStr.padStart(3, '0')
  }, [positionId])
  return (
    <div className={`text-gray-500 border border-gray-200 box-border flex items-center rounded-md italic text-[11px] pl-1 pr-1.5 font-medium ${className ?? ''}`}>
      <HashtagIcon className='w-3 h-3 text-gray-400 fill-current mr-1 stroke-current stroke-1' />
      {localPositionId}
    </div>
  )
}

type IQADocumentDetailProps = {
  embeddingAvailable: boolean
  qaInfo?: Partial<QADocumentDetail> & { id: string }
  onUpdate: (id: string, q: string, a: string) => void
  onCancel: () => void
}

/**
 * Show all the contents of the QADocument
 */
const QADocumentDetailComponent: FC<IQADocumentDetailProps> = ({
  embeddingAvailable,
  qaInfo,
  onUpdate,
  onCancel,
}) => {
  const { t } = useTranslation()
  const [isEditing, setIsEditing] = useState(false)
  const [question, setQuestion] = useState(qaInfo?.question || '')
  const [answer, setAnswer] = useState(qaInfo?.answer || '')
  const { eventEmitter } = useEventEmitterContextContext()
  const [loading, setLoading] = useState(false)

  eventEmitter?.useSubscription((v) => {
    if (v === 'update-qa')
      setLoading(true)
    else
      setLoading(false)
  })

  const handleCancel = () => {
    setIsEditing(false)
    setQuestion(qaInfo?.question || '')
    setAnswer(qaInfo?.answer || '')
  }
  const handleSave = () => {
    onUpdate(qaInfo?.id || '', question, answer)
  }

  const renderContent = () => {
    return (
      <>
        <div className='mb-1 text-xs font-medium text-gray-500'>QUESTION</div>
        <AutoHeightTextarea
          outerClassName='mb-4'
          className='leading-6 text-md text-gray-800'
          value={question}
          placeholder={t('datasetDocuments.segment.questionPlaceholder') || ''}
          onChange={e => setQuestion(e.target.value)}
          disabled={!isEditing}
        />
        <div className='mb-1 text-xs font-medium text-gray-500'>ANSWER</div>
        <AutoHeightTextarea
          outerClassName='mb-4'
          className='leading-6 text-md text-gray-800'
          value={answer}
          placeholder={t('datasetDocuments.segment.answerPlaceholder') || ''}
          onChange={e => setAnswer(e.target.value)}
          disabled={!isEditing}
          autoFocus
        />
      </>
    )
  }

  return (
    <div className={'flex flex-col relative'}>
      <div className='absolute right-0 top-0 flex items-center h-7'>
        {isEditing && (
          <>
            <Button
              className='mr-2 !h-7 !px-3 !py-[5px] text-xs font-medium text-gray-700 !rounded-md'
              onClick={handleCancel}>
              {t('common.operation.cancel')}
            </Button>
            <Button
              type='primary'
              className='!h-7 !px-3 !py-[5px] text-xs font-medium !rounded-md'
              onClick={handleSave}
              disabled={loading}
            >
              {t('common.operation.save')}
            </Button>
          </>
        )}
        {!isEditing && embeddingAvailable && (
          <>
            <div className='group relative flex justify-center items-center w-6 h-6 hover:bg-gray-100 rounded-md cursor-pointer'>
              <div className={cn(s.editTip, 'hidden items-center absolute -top-10 px-3 h-[34px] bg-white rounded-lg whitespace-nowrap text-xs font-semibold text-gray-700 group-hover:flex')}>{t('common.operation.edit')}</div>
              <Edit03 className='w-4 h-4 text-gray-500' onClick={() => setIsEditing(true)} />
            </div>
            <div className='mx-3 w-[1px] h-3 bg-gray-200' />
          </>
        )}
        <div className='flex justify-center items-center w-6 h-6 cursor-pointer' onClick={onCancel}>
          <XClose className='w-4 h-4 text-gray-500' />
        </div>
      </div>
      <QADocumentIndexTag positionId={qaInfo?.position || ''} className='w-fit mt-[2px] mb-6' />
      <div className={s.segModalContent}>{renderContent()}</div>
    </div>
  )
}
export const QADocumentDetailModal = memo(QADocumentDetailComponent)

export const SettingsIcon = ({ className }: SVGProps<SVGElement>) => {
  return <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" className={className ?? ''}>
    <path d="M2 5.33325L10 5.33325M10 5.33325C10 6.43782 10.8954 7.33325 12 7.33325C13.1046 7.33325 14 6.43782 14 5.33325C14 4.22868 13.1046 3.33325 12 3.33325C10.8954 3.33325 10 4.22868 10 5.33325ZM6 10.6666L14 10.6666M6 10.6666C6 11.7712 5.10457 12.6666 4 12.6666C2.89543 12.6666 2 11.7712 2 10.6666C2 9.56202 2.89543 8.66659 4 8.66659C5.10457 8.66659 6 9.56202 6 10.6666Z" stroke="#667085" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
}

// status item for list
export const StatusItem: FC<{
  status: boolean
  reverse?: boolean
  scene?: 'list' | 'detail'
  textCls?: string
  errorMessage?: string
}> = ({ status, reverse = false, scene = 'list', textCls = '', errorMessage }) => {
  const { t } = useTranslation()
  const localStatus = status ? { color: 'green', text: t('datasetDocuments.list.status.enabled') } : { color: 'red', text: t('datasetDocuments.list.status.error') }

  return <div className={
    cn('flex items-center',
      reverse ? 'flex-row-reverse' : '',
      scene === 'detail' ? s.statusItemDetail : '')
  }>
    <Indicator color={localStatus.color as IndicatorProps['color']} className={reverse ? 'ml-2' : 'mr-2'} />
    <span className={cn('text-gray-700 text-sm', textCls)}>{localStatus.text}</span>
    {
      errorMessage && (
        <Tooltip
          selector='dataset-document-detail-item-status'
          htmlContent={
            <div className='max-w-[260px] break-all'>{errorMessage}</div>
          }
        >
          <HelpCircle className='ml-1 w-[14px] h-[14px] text-gray-700' />
        </Tooltip>
      )
    }
  </div>
}

type OperationName = 'delete'

export const OperationAction: FC<{
  embeddingAvailable: boolean
  doc_id: string
  enabled: boolean
  datasetId: string
  onUpdate: (operationName?: string) => void
  scene?: 'list' | 'detail'
  className?: string
}> = ({ embeddingAvailable, datasetId, doc_id, onUpdate, scene = 'list', className = '' }) => {
  const [showModal, setShowModal] = useState(false)
  const { notify } = useContext(ToastContext)
  const { t } = useTranslation()
  const router = useRouter()

  const isListScene = scene === 'list'

  const onOperate = async (operationName: OperationName) => {
    let opApi = deleteQADocument
    switch (operationName) {
      case 'delete':
      default:
        opApi = deleteQADocument
        break
    }
    const [e] = await asyncRunSafe<CommonResponse>(opApi({ datasetId, documentId: doc_id }) as Promise<CommonResponse>)
    if (!e)
      notify({ type: 'success', message: t('common.actionMsg.modifiedSuccessfully') })
    else
      notify({ type: 'error', message: t('common.actionMsg.modificationFailed') })
    onUpdate(operationName)
  }
  return <div className='flex items-center' onClick={e => e.stopPropagation()}>
    {isListScene && !embeddingAvailable && (
      <Switch defaultValue={false} onChange={() => { }} disabled={true} size='md' />
    )}

    {embeddingAvailable && (
      <Popover
        htmlContent={
          <div className='w-full py-1'>
            <div className={cn(s.actionItem, s.deleteActionItem, 'group')} onClick={() => setShowModal(true)}>
              <TrashIcon className={'w-4 h-4 stroke-current text-gray-500 stroke-2 group-hover:text-red-500'} />
              <span className={cn(s.actionName, 'group-hover:text-red-500')}>{t('datasetDocuments.list.action.delete')}</span>
            </div>
          </div>
        }
        trigger='click'
        position='br'
        btnElement={
          <div className={cn(s.commonIcon)}>
            <DotsHorizontal className='w-4 h-4 text-gray-700' />
          </div>
        }
        btnClassName={open => cn(isListScene ? s.actionIconWrapperList : s.actionIconWrapperDetail, open ? '!bg-gray-100 !shadow-none' : '!bg-transparent')}
        className={`!w-[200px] h-fit !z-20 ${className}`}
      />
    )}

    {showModal && <Modal isShow={showModal} onClose={() => setShowModal(false)} className={s.delModal} closable>
      <div>
        <div className={s.warningWrapper}>
          <ExclamationCircleIcon className={s.warningIcon} />
        </div>
        <div className='text-xl font-semibold text-gray-900 mb-1'>{t('datasetDocuments.list.delete.title')}</div>
        <div className='text-sm text-gray-500 mb-10'>{t('datasetDocuments.list.delete.content')}</div>
        <div className='flex gap-2 justify-end'>
          <Button onClick={() => setShowModal(false)}>{t('common.operation.cancel')}</Button>
          <Button
            type='warning'
            onClick={() => onOperate('delete')}
            className='border-red-700 border-[0.5px]'
          >
            {t('common.operation.sure')}
          </Button>
        </div>
      </div>
    </Modal>}
  </div>
}

type LocalDoc = QADocumentDetail & { percent?: number }
type IDocumentListProps = {
  embeddingAvailable: boolean
  documents: LocalDoc[]
  datasetId: string
  onUpdate: () => void
}

/**
 * Document list component including basic information
 */
const DocumentList: FC<IDocumentListProps> = ({ embeddingAvailable, documents = [], datasetId, onUpdate }) => {
  const { t } = useTranslation()
  const router = useRouter()
  const [localDocs, setLocalDocs] = useState<LocalDoc[]>(documents)
  const [enableSort, setEnableSort] = useState(false)
  const { notify } = useContext(ToastContext)
  const [currQADocument, setCurrQADocument] = useState<{ qaInfo?: QADocumentDetail; showModal: boolean }>({ showModal: false })

  const onClickModal = (detail: QADocumentDetail) => {
    setCurrQADocument({ qaInfo: detail, showModal: true })
  }

  const onCloseModal = () => {
    setCurrQADocument({ ...currQADocument, showModal: false })
  }

  const { eventEmitter } = useEventEmitterContextContext()
  const handleUpdateQADocument = async (QAdocumentId: string, question: string, answer: string) => {
    const params: QADocumentUpdator = { question: '', answer: '' }
    if (!question.trim())
      return notify({ type: 'error', message: t('datasetDocuments.segment.questionEmpty') })
    if (!answer.trim())
      return notify({ type: 'error', message: t('datasetDocuments.segment.answerEmpty') })

    params.question = question
    params.answer = answer

    try {
      eventEmitter?.emit('update-qa')
      const res = await updateQADocument({ datasetId, QAdocumentId, body: params })
      notify({ type: 'success', message: t('common.actionMsg.modifiedSuccessfully') })
      onCloseModal()
    }
    finally {
      eventEmitter?.emit('')
    }
  }

  useEffect(() => {
    setLocalDocs(documents)
  }, [documents])

  const onClickSort = () => {
    setEnableSort(!enableSort)
    if (!enableSort) {
      const sortedDocs = [...localDocs].sort((a, b) => dayjs(a.created_at).isBefore(dayjs(b.created_at)) ? -1 : 1)
      setLocalDocs(sortedDocs)
    }
    else {
      setLocalDocs(documents)
    }
  }

  return (
    <>
      <table className={`w-full border-collapse border-0 text-sm mt-3 ${s.documentTable}`}>
        <thead className="h-8 leading-8 border-b border-gray-200 text-gray-500 font-medium text-xs uppercase">
          <tr>
            <td className='w-12'>#</td>
            <td>{t('datasetQADocuments.list.table.header.question')}</td>
            <td className='w-44'>
              <div className='flex justify-between items-center'>
                {t('datasetQADocuments.list.table.header.uploadTime')}
                <ArrowDownIcon className={cn('h-3 w-3 stroke-current stroke-2 cursor-pointer', enableSort ? 'text-gray-500' : 'text-gray-300')} onClick={onClickSort} />
              </div>
            </td>
            <td className='w-40'>{t('datasetQADocuments.list.table.header.status')}</td>
            <td className='w-20'>{t('datasetQADocuments.list.table.header.action')}</td>
          </tr>
        </thead>
        <tbody className="text-gray-700">
          {localDocs.map((doc) => {
            return <tr
              key={doc.id}
              className={'border-b border-gray-200 h-8 hover:bg-gray-50 cursor-pointer'}
              onClick={() => onClickModal(doc)}
            >
              <td className='text-left align-middle text-gray-500 text-xs'>{doc.position}</td>
              <td className={s.tdValue}>
                {doc.question}
              </td>
              <td className='text-gray-500 text-[13px]'>
                {dayjs.unix(doc.created_at).format(t('datasetHitTesting.dateTimeFormat') as string)}
              </td>
              <td>
                <StatusItem status={doc.enabled} errorMessage={doc.error} />
              </td>
              <td>
                <OperationAction
                  embeddingAvailable={embeddingAvailable}
                  datasetId={datasetId}
                  doc_id={doc.id}
                  enabled={doc.enabled}
                  onUpdate={onUpdate}
                />
              </td>
            </tr>
          })}
        </tbody>
      </table>
      <Modal isShow={currQADocument.showModal} onClose={() => {}} className='!max-w-[640px] !overflow-visible'>
        <QADocumentDetailComponent
          embeddingAvailable={embeddingAvailable}
          qaInfo={currQADocument.qaInfo ?? { id: '' }}
          onUpdate={handleUpdateQADocument}
          onCancel={onCloseModal}
        />
      </Modal>
    </>
  )
}

export default DocumentList
