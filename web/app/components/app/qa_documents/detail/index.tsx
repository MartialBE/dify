import { memo, useState } from 'react'
import type { FC } from 'react'
import { useTranslation } from 'react-i18next'
import { useContext } from 'use-context-selector'
import { useParams } from 'next/navigation'
import Modal from '@/app/components/base/modal'
import Button from '@/app/components/base/button'
import AutoHeightTextarea from '@/app/components/base/auto-height-textarea/common'
import { Hash02, XClose } from '@/app/components/base/icons/src/vender/line/general'
import { ToastContext } from '@/app/components/base/toast'
import type { QADocumentUpdator } from '@/models/datasets'
import { addQADocument } from '@/service/apps'

type AddQADocumentProps = {
  isShow: boolean
  onCancel: () => void
  onSave: () => void
}

const AddQADocumentModal: FC<AddQADocumentProps> = ({
  isShow,
  onCancel,
  onSave,
}) => {
  const { t } = useTranslation()
  const { notify } = useContext(ToastContext)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const { appId } = useParams()
  const [loading, setLoading] = useState(false)

  const handleCancel = () => {
    setQuestion('')
    setAnswer('')
    onCancel()
  }

  const handleSave = async () => {
    const params: QADocumentUpdator = { answer: '', question: '' }
    if (!question.trim())
      return notify({ type: 'error', message: t('datasetDocuments.segment.questionEmpty') })
    if (!answer.trim())
      return notify({ type: 'error', message: t('datasetDocuments.segment.answerEmpty') })

    params.question = question
    params.answer = answer

    setLoading(true)
    try {
      await addQADocument({ appId, body: params })
      notify({ type: 'success', message: t('common.actionMsg.modifiedSuccessfully') })
      handleCancel()
      onSave()
    }
    finally {
      setLoading(false)
    }
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
          autoFocus
        />
        <div className='mb-1 text-xs font-medium text-gray-500'>ANSWER</div>
        <AutoHeightTextarea
          outerClassName='mb-4'
          className='leading-6 text-md text-gray-800'
          value={answer}
          placeholder={t('datasetDocuments.segment.answerPlaceholder') || ''}
          onChange={e => setAnswer(e.target.value)}
        />
      </>
    )
  }

  return (
    <Modal isShow={isShow} onClose={() => {}} className='pt-8 px-8 pb-6 !max-w-[640px] !rounded-xl'>
      <div className={'flex flex-col relative'}>
        <div className='absolute right-0 -top-0.5 flex items-center h-6'>
          <div className='flex justify-center items-center w-6 h-6 cursor-pointer' onClick={handleCancel}>
            <XClose className='w-4 h-4 text-gray-500' />
          </div>
        </div>
        <div className='mb-[14px]'>
          <span className='inline-flex items-center px-1.5 h-5 border border-gray-200 rounded-md'>
            <Hash02 className='mr-0.5 w-3 h-3 text-gray-400' />
            <span className='text-[11px] font-medium text-gray-500 italic'>
              {t('datasetDocuments.segment.newQaSegment')}
            </span>
          </span>
        </div>
        <div className='mb-4 py-1.5 h-[420px] overflow-auto'>{renderContent()}</div>
        <div className='flex justify-end'>
          <Button
            className='mr-2 !h-9 !px-4 !py-2 text-sm font-medium text-gray-700 !rounded-lg'
            onClick={handleCancel}>
            {t('common.operation.cancel')}
          </Button>
          <Button
            type='primary'
            className='!h-9 !px-4 !py-2 text-sm font-medium !rounded-lg'
            onClick={handleSave}
            disabled={loading}
          >
            {t('common.operation.save')}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

export default memo(AddQADocumentModal)
