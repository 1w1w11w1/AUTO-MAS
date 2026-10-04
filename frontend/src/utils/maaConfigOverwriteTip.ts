import { translate as t } from '@/i18n'
import { Modal } from 'ant-design-vue'

/**
 * 配置 MAA 的会话真的起来之后提示一次：会用本账号的 MAS 存档覆盖 MAA 原生配置，
 * 会话前的配置已自动归档、可在账号编辑页的「配置恢复」里找回。
 *
 * 不做二次确认——托管与计划任务同样覆盖配置但没有按钮，弹窗挡不住那条路径。
 * 手动按钮路径（脚本页与账号编辑页）共用这一份，不再两处各写一遍。
 */
export function showMaaConfigOverwriteTip(): void {
  Modal.info({
    title: t('scripts.toast.maaConfigOverwriteTitle'),
    content: t('scripts.toast.maaConfigOverwriteContent'),
    okText: t('common.confirm'),
  })
}
