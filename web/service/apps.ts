import type { Fetcher } from 'swr'
import { del, get, post, put } from './base'
import type { ApikeysListResponse, AppDailyConversationsResponse, AppDailyEndUsersResponse, AppDetailResponse, AppListResponse, AppStatisticsResponse, AppTemplatesResponse, AppTokenCostsResponse, CreateApiKeyResponse, GenerationIntroductionResponse, UpdateAppModelConfigResponse, UpdateAppSiteCodeResponse, UpdateOpenAIKeyResponse, ValidateOpenAIKeyResponse } from '@/models/app'
import type { CommonResponse } from '@/models/common'
import type { AppMode, ModelConfig } from '@/types/app'
import type { QADocumentDetail, QADocumentListResponse, QADocumentUpdator } from '@/models/datasets'

export const fetchAppList: Fetcher<AppListResponse, { url: string; params?: Record<string, any> }> = ({ url, params }) => {
  return get(url, { params }) as Promise<AppListResponse>
}

export const fetchAppDetail: Fetcher<AppDetailResponse, { url: string; id: string }> = ({ url, id }) => {
  return get(`${url}/${id}`) as Promise<AppDetailResponse>
}

export const fetchAppTemplates: Fetcher<AppTemplatesResponse, { url: string }> = ({ url }) => {
  return get(url) as Promise<AppTemplatesResponse>
}

export const createApp: Fetcher<AppDetailResponse, { name: string; icon: string; icon_background: string; mode: AppMode; config?: ModelConfig }> = ({ name, icon, icon_background, mode, config }) => {
  return post('apps', { body: { name, icon, icon_background, mode, model_config: config } }) as Promise<AppDetailResponse>
}

export const deleteApp: Fetcher<CommonResponse, string> = (appID) => {
  return del(`apps/${appID}`) as Promise<CommonResponse>
}

export const updateAppSiteStatus: Fetcher<AppDetailResponse, { url: string; body: Record<string, any> }> = ({ url, body }) => {
  return post(url, { body }) as Promise<AppDetailResponse>
}

export const updateAppApiStatus: Fetcher<AppDetailResponse, { url: string; body: Record<string, any> }> = ({ url, body }) => {
  return post(url, { body }) as Promise<AppDetailResponse>
}

// path: /apps/{appId}/rate-limit
export const updateAppRateLimit: Fetcher<AppDetailResponse, { url: string; body: Record<string, any> }> = ({ url, body }) => {
  return post(url, { body }) as Promise<AppDetailResponse>
}

export const updateAppSiteAccessToken: Fetcher<UpdateAppSiteCodeResponse, { url: string }> = ({ url }) => {
  return post(url) as Promise<UpdateAppSiteCodeResponse>
}

export const updateAppSiteConfig: Fetcher<AppDetailResponse, { url: string; body: Record<string, any> }> = ({ url, body }) => {
  return post(url, { body }) as Promise<AppDetailResponse>
}

export const getAppDailyConversations: Fetcher<AppDailyConversationsResponse, { url: string; params: Record<string, any> }> = ({ url, params }) => {
  return get(url, { params }) as Promise<AppDailyConversationsResponse>
}

export const getAppStatistics: Fetcher<AppStatisticsResponse, { url: string; params: Record<string, any> }> = ({ url, params }) => {
  return get(url, { params }) as Promise<AppStatisticsResponse>
}

export const getAppDailyEndUsers: Fetcher<AppDailyEndUsersResponse, { url: string; params: Record<string, any> }> = ({ url, params }) => {
  return get(url, { params }) as Promise<AppDailyEndUsersResponse>
}

export const getAppTokenCosts: Fetcher<AppTokenCostsResponse, { url: string; params: Record<string, any> }> = ({ url, params }) => {
  return get(url, { params }) as Promise<AppTokenCostsResponse>
}

export const updateAppModelConfig: Fetcher<UpdateAppModelConfigResponse, { url: string; body: Record<string, any> }> = ({ url, body }) => {
  return post(url, { body }) as Promise<UpdateAppModelConfigResponse>
}

// For temp testing
export const fetchAppListNoMock: Fetcher<AppListResponse, { url: string; params: Record<string, any> }> = ({ url, params }) => {
  return get(url, params) as Promise<AppListResponse>
}

export const fetchApiKeysList: Fetcher<ApikeysListResponse, { url: string; params: Record<string, any> }> = ({ url, params }) => {
  return get(url, params) as Promise<ApikeysListResponse>
}

export const delApikey: Fetcher<CommonResponse, { url: string; params: Record<string, any> }> = ({ url, params }) => {
  return del(url, params) as Promise<CommonResponse>
}

export const createApikey: Fetcher<CreateApiKeyResponse, { url: string; body: Record<string, any> }> = ({ url, body }) => {
  return post(url, body) as Promise<CreateApiKeyResponse>
}

export const validateOpenAIKey: Fetcher<ValidateOpenAIKeyResponse, { url: string; body: { token: string } }> = ({ url, body }) => {
  return post(url, { body }) as Promise<ValidateOpenAIKeyResponse>
}

export const updateOpenAIKey: Fetcher<UpdateOpenAIKeyResponse, { url: string; body: { token: string } }> = ({ url, body }) => {
  return post(url, { body }) as Promise<UpdateOpenAIKeyResponse>
}

export const generationIntroduction: Fetcher<GenerationIntroductionResponse, { url: string; body: { prompt_template: string } }> = ({ url, body }) => {
  return post(url, { body }) as Promise<GenerationIntroductionResponse>
}

export type SortType = 'created_at' | '-created_at'

export const fetchQADocuments: Fetcher<QADocumentListResponse, { appId: string; params: { keyword: string; page: number; limit: number; sort?: SortType } }> = ({ appId, params }) => {
  return get(`/apps/${appId}/qa_documents`, { params }) as Promise<QADocumentListResponse>
}

export const fetchQADocumentDetail: Fetcher<QADocumentDetail, { appId: string; QAdocumentId: string }> = ({ appId, QAdocumentId }) => {
  return get(`/apps/${appId}/qa_documents/${QAdocumentId}`) as Promise<QADocumentDetail>
}

export const addQADocument: Fetcher<{ data: QADocumentDetail }, { appId: string; body: QADocumentUpdator }> = ({ appId, body }) => {
  return post(`/apps/${appId}/qa_documents`, { body }) as Promise<{ data: QADocumentDetail }>
}

export const updateQADocument: Fetcher<{ data: QADocumentDetail }, { appId: string; QAdocumentId: string; body: QADocumentUpdator }> = ({ appId, QAdocumentId, body }) => {
  return put(`/apps/${appId}/qa_documents/${QAdocumentId}`, { body }) as Promise<{ data: QADocumentDetail }>
}

export const deleteQADocument: Fetcher<CommonResponse, { appId: string; QAdocumentId: string }> = ({ appId, QAdocumentId }) => {
  return del(`/apps/${appId}/qa_documents/${QAdocumentId}`) as Promise<CommonResponse>
}
