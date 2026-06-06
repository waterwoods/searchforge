import { Alert } from 'antd';
import { isLabPath } from '../../routes/labPages';
import { isUnifiedIntakeProductOnlyUi } from '../../config/productSurface';

type Props = { pathname: string };

/** Visible on lab/dev routes when not building product-only UI. */
export function LabDevBanner({ pathname }: Props) {
    if (isUnifiedIntakeProductOnlyUi() || !isLabPath(pathname)) {
        return null;
    }
    return (
        <Alert
            type="warning"
            showIcon
            banner
            message="Internal / lab surface — not broker product"
            description="SearchForge R&D and founder tools. Paid pilot UI uses /workbench/unified-intake only."
            style={{ margin: 0, borderRadius: 0 }}
        />
    );
}
