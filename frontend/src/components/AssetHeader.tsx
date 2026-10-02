import type { Load } from "../api/resource";
import type { AssetDetail } from "../api/types";
import { TEXTOS } from "../content/textos";
import { formatCurrency, formatDate } from "../format/numbers";
import { textFor, useReading } from "../reading";
import { SectionError, SectionSkeleton } from "./SectionStatus";

type Props = {
  load: Load<AssetDetail>;
  onRetry: () => void;
};

/**
 * O cabeçalho (RF-07, camada 1): código, nome de pregão, nome, as tags de tipo e situação, o
 * segmento de listagem, setor › subsetor › segmento (o nulo é omitido) e o último fechamento
 * com a data — ou "sem preço coletado ainda". O `404` não chega aqui: a tela inteira vira
 * "ativo não encontrado".
 */
export function AssetHeader({ load, onRetry }: Props) {
  // O nível muda só a frase do último fechamento, nunca o valor (D-152, V-04).
  const reading = useReading();
  if (load.state !== "ok") {
    return (
      <section
        className="ruvor-asset-head"
        aria-busy={load.state === "loading" || undefined}
      >
        <div className="ruvor-asset-head__id">
          {load.state === "loading" ? (
            <SectionSkeleton />
          ) : (
            <SectionError onRetry={onRetry} />
          )}
        </div>
      </section>
    );
  }

  const asset = load.data;
  // Setor › subsetor › segmento: o nível nulo sai, sem traço. O nível é a chave — dois
  // níveis podem ter o mesmo nome.
  const levels: Array<[string, string | null]> = [
    ["sector", asset.sector],
    ["subsector", asset.subsector],
    ["segment", asset.segment],
  ];
  const crumbs = levels.filter(
    (crumb): crumb is [string, string] => crumb[1] !== null && crumb[1] !== "",
  );
  const last = asset.last_price;

  return (
    <section className="ruvor-asset-head">
      <div className="ruvor-asset-head__id">
        <p className="ruvor-eyebrow">{asset.trading_name}</p>
        <h1 className="ruvor-display">{asset.ticker}</h1>
        <p className="ruvor-asset-head__name">{asset.name}</p>
        <div className="ruvor-asset-head__tags">
          <span className="ruvor-tag ruvor-tag--evidence">
            {TEXTOS[`ativo.tipo.${asset.kind}`]}
          </span>
          <span
            className={
              asset.status === "active"
                ? "ruvor-tag ruvor-tag--validated"
                : "ruvor-tag ruvor-tag--review"
            }
          >
            {TEXTOS[`ativo.situacao.${asset.status}`]}
          </span>
          {asset.listing_segment !== null && asset.listing_segment !== "" && (
            <span className="ruvor-tag ruvor-tag--neutral">
              {TEXTOS["ativo.listagem"](asset.listing_segment)}
            </span>
          )}
        </div>
        {crumbs.length > 0 && (
          <ol className="ruvor-crumbs" aria-label={TEXTOS["ativo.classificacao"]}>
            {crumbs.map(([level, part]) => (
              <li key={level}>{part}</li>
            ))}
          </ol>
        )}
      </div>
      <div className="ruvor-panel ruvor-asset-head__last">
        <p className="ruvor-eyebrow">{TEXTOS["ativo.ultimoFechamento.rotulo"]}</p>
        {last !== null ? (
          <>
            <p className="ruvor-asset-head__value ruvor-num" data-value="last-close">
              {formatCurrency(Number(last.close))}
            </p>
            <p className="ruvor-note">
              {textFor("ativo.ultimoFechamento", reading)(formatDate(last.date))}
            </p>
          </>
        ) : (
          <>
            <p className="ruvor-asset-head__value" data-value="last-close">
              —
            </p>
            <p className="ruvor-note">{TEXTOS["ativo.semPreco"]}</p>
          </>
        )}
      </div>
    </section>
  );
}
