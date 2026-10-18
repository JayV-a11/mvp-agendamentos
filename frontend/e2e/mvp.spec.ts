import { test, expect, Page } from '@playwright/test';
import { accessibility } from './accessibility';

test('fluxo completo público e administrativo, acessibilidade básica e estados reais', async ({
  page,
  browser,
}, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  async function capture(name: string, target = page) {
    await accessibility(target);
    await target.screenshot({ path: testInfo.outputPath(`${name}.png`), fullPage: true });
  }
  async function fits(target = page) {
    expect(
      await target.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    ).toBe(true);
  }
  await page.goto('/admin/agenda');
  await expect(page.getByRole('heading', { name: 'Bem-vinda de volta' })).toBeVisible();
  await capture('01-login');
  await page.keyboard.press('Tab');
  await expect(page.locator('.skip-link')).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('main')).toBeFocused();
  await expect(page).toHaveURL(/\/login$/);
  await page.keyboard.press('Tab');
  await expect(page.getByLabel('E-mail', { exact: true })).toBeFocused();
  await page.getByLabel('E-mail', { exact: true }).fill(process.env['E2E_EMAIL']!);
  await page.getByLabel('Senha', { exact: true }).fill('senha-incorreta');
  await page.getByRole('button', { name: 'Entrar na administração' }).click();
  await expect(page.getByRole('alert')).toBeVisible();
  await page.getByLabel('Senha', { exact: true }).fill(process.env['E2E_PASSWORD']!);
  await page.getByRole('button', { name: 'Entrar na administração' }).click();
  await expect(page.getByRole('heading', { name: 'Minha agenda' })).toBeVisible();
  await page
    .getByRole('navigation', { name: 'Administração' })
    .getByRole('link', { name: 'Catálogo', exact: true })
    .click();
  for (const [name, description, price, minutes] of [
    ['Box Braids', 'Tranças individuais longas', '180', '240'],
    ['Trança Nagô', 'Tranças rente à raiz', '90', '120'],
    ['Trança Twist', 'Tranças com efeito torcido', '150', '180'],
  ]) {
    await page.getByRole('button', { name: '+ Cadastrar novo serviço' }).click();
    await page.getByLabel('Nome', { exact: true }).fill(name);
    await page.getByLabel('Descrição (opcional)').fill(description);
    await page.getByLabel('Preço (R$)').fill(price);
    await page.getByLabel('Duração estimada (minutos)').fill(minutes);
    await page.getByRole('button', { name: 'Salvar serviço', exact: true }).click();
    await expect(page.locator('.alert.success')).toContainText('Serviço salvo com sucesso.');
  }
  await capture('02-gerenciar-catalogo');
  await fits();
  await page
    .getByRole('navigation', { name: 'Administração' })
    .getByRole('link', { name: 'Agenda', exact: true })
    .click();
  for (const [inicio, fim] of [
    ['2030-10-30T14:00', '2030-10-30T18:00'],
    ['2030-10-31T10:00', '2030-10-31T14:00'],
  ]) {
    await page.getByRole('button', { name: '+ Disponibilizar horário' }).click();
    await page.getByLabel('Início', { exact: true }).fill(inicio);
    await page.getByLabel('Fim', { exact: true }).fill(fim);
    await page.getByRole('button', { name: 'Salvar horário', exact: true }).click();
    await expect(page.locator('.alert.success')).toContainText('Horário disponibilizado.');
  }
  const context = await browser.newContext({
    baseURL: process.env['E2E_BASE_URL'],
    viewport: { width: 390, height: 844 },
    locale: 'pt-BR',
    timezoneId: 'Asia/Tokyo',
  });
  const client = await context.newPage();
  client.on('pageerror', (error) => errors.push(error.message));
  try {
    await client.goto('/');
    await expect(client.getByRole('heading', { name: 'Box Braids', exact: true })).toBeVisible();
    await capture('03-catalogo-publico', client);
    await client.getByRole('link', { name: 'Agendar este serviço: Box Braids' }).click();
    await expect(client.getByRole('button', { name: /14:00 – 18:00/ })).toBeVisible();
    await expect(
      client.getByRole('combobox', { name: 'Data desejada' }).locator('option:checked'),
    ).toHaveText('30/10/2030');
    await client.getByRole('button', { name: 'Enviar solicitação', exact: true }).click();
    await expect(client.getByText('Informe seu nome, com até 150 caracteres.')).toBeVisible();
    await client.getByRole('button', { name: /14:00 – 18:00/ }).click();
    await client.getByLabel('Nome completo').fill('Cliente Exemplo');
    await client.getByLabel('Telefone para contato').fill('(11) 99999-0000');
    await capture('04-solicitar-agendamento', client);
    await client.getByRole('button', { name: 'Enviar solicitação', exact: true }).click();
    await expect(client.getByRole('heading', { name: '✓ Solicitação enviada!' })).toBeVisible();
    await expect(client.getByText('Status: Pendente.', { exact: false })).toBeVisible();
    await capture('05-confirmacao-pendente', client);
    await page.reload();
    await expect(page.getByRole('heading', { name: 'Cliente Exemplo', exact: true })).toBeVisible();
    await page.getByRole('button', { name: '✓ Aprovar pedido de Cliente Exemplo' }).click();
    await expect(page.locator('.alert.success')).toContainText('aprovado');
    await client.getByRole('link', { name: '← Voltar ao catálogo', exact: true }).click();
    await client.getByRole('link', { name: 'Agendar este serviço: Box Braids' }).click();
    await expect(client.getByRole('button', { name: /10:00 – 14:00/ })).toBeVisible();
    await expect(client.getByRole('button', { name: /14:00 – 18:00/ })).toHaveCount(0);
    await client.getByRole('button', { name: /10:00 – 14:00/ }).click();
    await client.getByLabel('Nome completo').fill('Cliente Teste');
    await client.getByLabel('Telefone para contato').fill('11999990001');
    await client.getByRole('button', { name: 'Enviar solicitação', exact: true }).click();
    await expect(client.getByRole('heading', { name: '✓ Solicitação enviada!' })).toBeVisible();
    await page.reload();
    await expect(page.getByRole('heading', { name: 'Cliente Teste', exact: true })).toBeVisible();
    await capture('06-agenda-administrativa');
    await page.getByRole('button', { name: 'Recusar pedido de Cliente Teste' }).click();
    await expect(page.locator('.alert.success')).toContainText('recusado');
    await page.getByRole('button', { name: 'Cancelar atendimento de Cliente Exemplo' }).click();
    await expect(page.locator('.alert.success')).toContainText('cancelado');
    await page.getByRole('button', { name: 'Bloquear horário', exact: true }).first().click();
    await expect(page.locator('.alert.success')).toContainText('bloqueado');
    await page.getByRole('button', { name: 'Desbloquear horário', exact: true }).click();
    await expect(page.locator('.alert.success')).toContainText('desbloqueado');
    await page
      .getByRole('navigation', { name: 'Administração' })
      .getByRole('link', { name: 'Catálogo', exact: true })
      .click();
    await page.getByRole('button', { name: 'Desativar Box Braids', exact: true }).click();
    await expect(page.locator('.alert.success')).toContainText('desativado');
    await client.goto('/');
    await expect(client.getByRole('heading', { name: 'Box Braids', exact: true })).toHaveCount(0);
    await page.getByRole('button', { name: 'Reativar Box Braids', exact: true }).click();
    await expect(page.locator('.alert.success')).toContainText('reativado');
    await page.getByRole('button', { name: 'Editar Box Braids', exact: true }).click();
    if (process.env['E2E_STORAGE'] === '1') {
      await page.getByLabel('Fotografia (opcional)').setInputFiles({
        name: 'foto-sintetica.png',
        mimeType: 'image/png',
        buffer: Buffer.from(process.env['E2E_PHOTO_BASE64']!, 'base64'),
      });
    }
    await page.getByLabel('Preço (R$)').fill('200,00');
    await page.getByRole('button', { name: 'Salvar serviço', exact: true }).click();
    await expect(page.locator('.alert.success')).toContainText('salvo');
    if (process.env['E2E_STORAGE'] === '1') {
      await page.getByRole('button', { name: 'Editar Box Braids', exact: true }).click();
      await page.getByRole('button', { name: 'Remover foto atual' }).click();
      await expect(page.locator('.alert.success')).toContainText('Foto removida.');
      await page.getByRole('button', { name: 'Fechar formulário' }).click();
    }
    await client.goto('/');
    await expect(client.getByText(/R\$\s*200,00/)).toBeVisible();
    for (const path of ['/', '/login']) {
      await client.goto(path);
      await client.setViewportSize({ width: 320, height: 844 });
      await fits(client);
      await capture(path === '/' ? '07-catalogo-320px' : '08-login-320px', client);
    }
    await client.setViewportSize({ width: 780, height: 900 });
    await client.evaluate(() => (document.body.style.zoom = '2'));
    await fits(client);
    await expect(client.getByLabel('E-mail', { exact: true })).toBeVisible();
    await client.evaluate(() => (document.body.style.zoom = ''));
    await page.getByRole('button', { name: 'Sair', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Bem-vinda de volta' })).toBeVisible();
    await page.goto('/admin/servicos');
    await expect(page.getByRole('heading', { name: 'Bem-vinda de volta' })).toBeVisible();
    expect(errors).toEqual([]);
  } finally {
    await context.close();
  }
});
