import { LoaderCircleIcon, LockIcon, SparklesIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { InlineError } from "@/components/general/InlineError";
import { AzureEndpointDialog } from "@/components/page-specific/assessment/AzureEndpointDialog";
import { ExplanationSettings } from "@/components/page-specific/assessment/ExplanationSettings";
import { InterpretationText } from "@/components/page-specific/assessment/InterpretationText";
import { Button } from "@/components/ui/button";
import {
  EXPLANATION_STATUS,
  EXPLANATION_TEXT,
  EXPLANATION_TOAST,
} from "@/constants/explanation.constants";
import {
  useExplanation,
  useExplanationProviders,
} from "@/hooks/explanation.hook";
import type { AnalysisRequest } from "@/interfaces/aggregation.interface";
import { useProjectStore } from "@/store/project.store";
import { errorMessage } from "@/utils/api.utils";

/**
 * AI interpretation of the results snapshot. The API key stays in this component's state, is only
 * sent in the request body and is cleared after success and after failure (legacy). Providers and
 * models come from the API; a provider change resets the model. Failures are shown in a toast.
 */
export function ExplanationPanel({ snapshot }: { snapshot: AnalysisRequest }) {
  const providers = useExplanationProviders();
  const setInterpretationText = useProjectStore(
    (state) => state.setInterpretationText,
  );
  const [providerId, setProviderId] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  // null = the provider's default model (empty for Azure's free-text deployment name).
  const [modelChoice, setModelChoice] = useState<string | null>(null);
  const [azureEndpoint, setAzureEndpoint] = useState("");
  const [askEndpoint, setAskEndpoint] = useState(false);
  const [status, setStatus] = useState("");
  const [missingKey, setMissingKey] = useState(false);
  const [output, setOutput] = useState(
    () => useProjectStore.getState().interpretationText,
  );
  const explanation = useExplanation();
  const list = providers.data ?? [];
  const provider = list.find((item) => item.id === providerId) ?? list[0];
  const model = modelChoice ?? provider?.default_model ?? "";
  const isAzure = provider?.free_text_model ?? false;
  const canGenerate =
    !!provider && !explanation.isPending && (!isAzure || !!model.trim());

  const send = (endpoint: string | null) => {
    if (!provider) return;
    setStatus(EXPLANATION_STATUS.PENDING(provider.label, model.trim()));
    setOutput("");
    setInterpretationText("");
    explanation.generate(
      {
        analysis: snapshot,
        provider: provider.id,
        api_key: apiKey.trim(),
        model: model.trim() || null,
        azure_endpoint: endpoint,
      },
      {
        onSuccess: (data) => {
          setApiKey("");
          setStatus(EXPLANATION_STATUS.DONE);
          setOutput(data.text);
          setInterpretationText(data.text);
        },
        onError: (error) => {
          setApiKey("");
          setStatus(EXPLANATION_STATUS.ERROR);
          toast.error(EXPLANATION_TOAST.ERROR_TITLE, {
            description: errorMessage(error),
          });
        },
      },
    );
  };

  const start = () => {
    setMissingKey(false);
    if (!apiKey.trim()) {
      setMissingKey(true);
      return;
    }
    if (isAzure) setAskEndpoint(true);
    else send(null);
  };

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h3 className="font-semibold">{EXPLANATION_TEXT.TITLE}</h3>
        <p className="text-sm text-muted-foreground">{EXPLANATION_TEXT.NOTE}</p>
      </div>
      <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
        <LockIcon className="mt-px size-3.5 shrink-0" aria-hidden="true" />
        {EXPLANATION_TEXT.KEY_PRIVACY}
      </p>
      <InlineError
        message={providers.isError ? EXPLANATION_TEXT.PROVIDERS_ERROR : null}
      />
      {provider && (
        <ExplanationSettings
          providers={list}
          provider={provider}
          apiKey={apiKey}
          model={model}
          onProviderChange={(id) => {
            setProviderId(id);
            setModelChoice(null);
          }}
          onApiKeyChange={setApiKey}
          onModelChange={setModelChoice}
        />
      )}
      <InlineError
        title={missingKey ? EXPLANATION_STATUS.MISSING_KEY_TITLE : null}
        message={missingKey ? EXPLANATION_STATUS.MISSING_KEY : null}
      />
      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          onClick={start}
          disabled={!canGenerate}
          aria-busy={explanation.isPending}
        >
          {explanation.isPending ? (
            <LoaderCircleIcon
              className="animate-spin"
              data-icon="inline-start"
            />
          ) : (
            <SparklesIcon data-icon="inline-start" />
          )}
          {explanation.isPending
            ? EXPLANATION_TEXT.GENERATING
            : EXPLANATION_TEXT.GENERATE}
        </Button>
        <output className="text-sm text-muted-foreground">{status}</output>
      </div>
      <InterpretationText text={output} />
      {askEndpoint && (
        <AzureEndpointDialog
          open
          initialEndpoint={azureEndpoint}
          onSubmit={(endpoint) => {
            setAskEndpoint(false);
            if (!endpoint) {
              setStatus(EXPLANATION_STATUS.MISSING_ENDPOINT);
              return;
            }
            setAzureEndpoint(endpoint);
            send(endpoint);
          }}
          onCancel={() => {
            setAskEndpoint(false);
            setStatus(EXPLANATION_STATUS.MISSING_ENDPOINT);
          }}
        />
      )}
    </div>
  );
}
