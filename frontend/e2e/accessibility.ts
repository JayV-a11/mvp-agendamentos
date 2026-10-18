import { expect, Page } from '@playwright/test';

/** Verificações objetivas; não substituem avaliação humana com leitor de tela. */
export async function accessibility(page: Page) {
  const issues = await page.evaluate(() => {
    const problems: string[] = [];
    const visible = (element: Element) => {
      const rect = element.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && getComputedStyle(element).visibility !== 'hidden';
    };
    const rgb = (color: string) =>
      color
        .match(/[\d.]+/g)!
        .slice(0, 3)
        .map(Number);
    const luminance = (color: number[]) =>
      color
        .map((c) => c / 255)
        .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
        .reduce((sum, c, i) => sum + c * [0.2126, 0.7152, 0.0722][i], 0);
    const contrast = (a: number[], b: number[]) => {
      const l1 = luminance(a),
        l2 = luminance(b);
      return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    };
    const background = (element: Element): number[] => {
      let current: Element | null = element;
      while (current) {
        const color = getComputedStyle(current).backgroundColor;
        if (color !== 'rgba(0, 0, 0, 0)' && color !== 'transparent') return rgb(color);
        current = current.parentElement;
      }
      return [255, 255, 255];
    };
    for (const element of document.querySelectorAll<HTMLElement>(
      'main button,main a,main input,main select,main textarea',
    )) {
      if (!visible(element)) continue;
      let target: Element = element;
      if (element instanceof HTMLInputElement && element.type === 'checkbox')
        target = element.labels![0];
      const rect = target.getBoundingClientRect();
      if (rect.width < 44 || rect.height < 44)
        problems.push(`Área de toque menor que 44px: ${element.id || element.textContent?.trim()}`);
      if (
        (element instanceof HTMLInputElement ||
          element instanceof HTMLSelectElement ||
          element instanceof HTMLTextAreaElement) &&
        !element.labels?.length
      )
        problems.push(`Campo sem rótulo: ${element.id}`);
    }
    for (const element of document.querySelectorAll<HTMLElement>(
      'main h1,main h2,main h3,main p,main label,main legend,main button,main a,main .badge,main .brand-mark',
    )) {
      if (
        !visible(element) ||
        !element.textContent?.trim() ||
        (element as HTMLButtonElement).disabled
      )
        continue;
      const style = getComputedStyle(element);
      const large =
        parseFloat(style.fontSize) >= 24 ||
        (parseFloat(style.fontSize) >= 18.66 && Number(style.fontWeight) >= 700);
      const ratio = contrast(rgb(style.color), background(element));
      if (ratio < (large ? 3 : 4.5))
        problems.push(`Contraste ${ratio.toFixed(2)}: ${element.textContent.trim().slice(0, 45)}`);
    }
    for (const element of document.querySelectorAll<HTMLElement>(
      'main input:not([type=checkbox]),main select,main textarea,main .slot-button',
    )) {
      if (!visible(element) || (element as HTMLInputElement).disabled) continue;
      const ratio = contrast(
        rgb(getComputedStyle(element).borderColor),
        background(element.parentElement!),
      );
      if (ratio < 3)
        problems.push(
          `Contorno com contraste ${ratio.toFixed(2)}: ${element.id || element.textContent?.trim()}`,
        );
    }
    for (const image of document.querySelectorAll('main img'))
      if (!image.alt) problems.push('Imagem sem texto alternativo');
    return problems;
  });
  expect(issues).toEqual([]);
}
