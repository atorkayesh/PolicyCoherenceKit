import { Card, CardContent } from "@/components/ui/card";

/** One result card: a title, the main text (policy or pair), a value line and a caption. */
export function SignalCard({
  title,
  main,
  value,
  caption,
  help,
}: {
  title: string;
  main: string;
  value: string;
  caption?: string;
  help?: string;
}) {
  return (
    <Card className="h-full">
      <CardContent className="flex flex-col gap-1">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="text-lg font-semibold wrap-break-word">{main}</p>
        <p className="text-sm font-medium">{value}</p>
        {caption && <p className="text-xs text-muted-foreground">{caption}</p>}
        {help && <p className="text-xs text-muted-foreground">{help}</p>}
      </CardContent>
    </Card>
  );
}
