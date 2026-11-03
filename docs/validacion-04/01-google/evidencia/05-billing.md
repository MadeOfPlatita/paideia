# Billing

This guide provides an overview of different Gemini API billing options, explains how to enable billing and monitor usage, and provides answers to frequently asked questions (FAQs) about billing.

## About billing and tiers

Billing for the Gemini API is based on your payment history.

| Usage tier | Qualification | Billing tier cap |
|---|---|---|
| **Free** | [Active project](/gemini-api/docs/api-key#google-cloud-projects) or free trial | N/A |
| **Tier 1** | Set up and link an active billing account | $250 |
| **Tier 2** | Paid $100 + 3 days from first successful payment | $2,000 |
| **Tier 3** | Paid $1,000 + 30 days from first successful payment | $20,000 - $100,000+ |
New accounts begin on the Free Tier, which allows access to [certain models](/gemini-api/docs/pricing) in the Gemini API and AI Studio, up to the models' free tier [rate limits](https://aistudio.google.com/rate-limit).

To deploy your applications directly from Build mode, eligible accounts can use the **Google Cloud Starter Tier**. This tier lets you publish up to 2 full-stack applications without setting up a Google Cloud project or billing account. See [Deploying from Google AI Studio](/gemini-api/docs/aistudio-deploying#starter-tier-eligibility) for eligibility details and refer to the [Google Cloud Starter Tier documentation](https://docs.cloud.google.com/docs/starter-tier) for more information.

To access higher rate limits, use advanced models, and ensure your prompts and responses are **not** used to improve Google products*, you can link a billing account and Prepay to move to the Paid Tiers. Then, you'll move through higher tiers based on cumulative spend and account age.

Tiers, rate limits, and billing account caps are all determined at the billing account level.

* *Enterprise-grade data privacy: For more information on data use for paid services, see the [Terms of Service](/gemini-api/terms#data-use-paid).*

## Set up billing to access the Paid Tier

You can create a project and set up billing, or import an existing project, to upgrade to the Paid Tier in [Google AI Studio](https://aistudio.google.com/projects). Upgrading from the Free Tier to the Paid Tier means linking a billing account and prepaying to add a minimum of $5 (or equivalent in other currencies) of credits to your account.

1. Go to the AI Studio [API keys](https://aistudio.google.com/api-keys) page, [Projects](https://aistudio.google.com/projects) page, or anywhere you see **Set up billing** button in AI Studio.
  - New users will have a [project and API key](/gemini-api/docs/api-key#google-cloud-projects) created for them by default.
  - If you need a new key, click [**Create API key**](https://aistudio.google.com/api-keys) and follow the dialog to add a key-project pair to the table.
2. Find the Free Tier project you want to upgrade to the Paid Tier, and click **Set up billing** under the *Billing Tier* column.
3. If you've never set up a Google billing account before:
  - You'll be asked to select your country to agree to the Terms of Service.
  - Then, fill in or confirm your contact information and payment method to continue.
4. If you have set up Google billing accounts in the past:
  - You'll be asked to choose from your existing billing accounts.
  - If you don't want to use any of your existing accounts, click **Add new billing account** and fill in or confirm your contact information and payment method to continue.
5. Next, you will either be:
  - Asked to prepay a minimum of $5 to complete billing setup (meaning your account is auto-assigned to the Prepay billing plan),
  - Given the choice between Prepay and Postpay billing plans for your account.
  - Assigned to a Postpay billing plan for an intermediary period until the new Prepay system propagates to all users (starting March 23, 2026).
6. After prepaying or selecting Postpay, your account setup is complete.

### Upgrade to the next paid tier

If you're already on a paid tier and meet the criteria for a plan change, you will be automatically upgraded to the next tier (subject to processing times).

## Verify billing status

After you have linked a billing account to your project, you can monitor its status on the [AI Studio Billing page](https://aistudio.google.com/billing). Unlike the free tier, paid tier status is dynamic; while your usage tier is determined by your account history, the Gemini API will only serve requests if you have a positive Prepay credit balance.

On the [Projects](https://aistudio.google.com/projects) page, you'll be able to see your project's tier and billing plan under the *Billing Tier* column. Any billing status actions you may need to take for a project display in the *Billing Tier* or *Status* columns:

- "***Set up billing***" if the project doesn't have a billing account attached.
- "***Set up Prepay***" if the project does have a billing account attached, but is required to use a Prepay billing plan that needs to be set up.
- "***No credits***" if the billing account is required to purchase credits but the Prepay payments account isn't set up or the available credit balance is depleted.
Click any of the messages to proceed with the necessary actions.

## Monitor usage

You can monitor your usage of the Gemini API in [Google AI Studio](https://aistudio.google.com/usage) in **Dashboard** > **Usage**.

## Billing plans

Billing plans for the Gemini API and AI Studio fall into two categories that determine when you pay for usage: Prepay and Postpay. You can check your assigned billing plan and manage payment methods on the [AI Studio Billing](https://aistudio.google.com/billing) page.

### Prepay

In the Prepay billing plan, you purchase credits towards your prepay balance in advance of your Gemini API usage, and your API usage costs are deducted from your Prepay credit balance in near real-time. You can prepay by adding credits into your account, or setting up auto-reload. After credits are purchased, unused credits expire after 12 months and are non-refundable, except after switching to a Postpay account.

When your Prepay credit balance on the billing account hits $0, all API keys in all projects linked to that billing account will stop working simultaneously. Requests then fail with an [HTTP 402 Payment Required](/gemini-api/docs/api-errors) error until you add credits. Prepay credits apply only to Gemini API usage costs; you can't use them to pay for other Google Cloud services.

New users default to the Prepay billing plan. Projects that pre-date the introduction of Prepay and Postpay billing plans may need to update their project's billing details before continuing to use the Gemini API.

*Note that Prepay is not available for [Invoiced (or Offline)](https://docs.cloud.google.com/billing/docs/concepts#billing_account_types) accounts.*

#### Add Prepay to an existing Postpay account

If your existing Cloud Billing account uses a **Postpay** plan, you can add **Prepay** capabilities to purchase credits in advance. These prepay credits let you use the Gemini API without creating a new Cloud Billing account.

During the setup to add **Prepay** to an existing account, you are presented with a mandatory confirmation screen explaining that your selected Cloud Billing account will be modified.

The system must modify your account state *before* you submit your prepayment. Therefore, canceling the process after confirming the modification but before completing the prepayment setup might result in temporary service disruptions for projects already linked to that Cloud Billing account. Ensure you are ready to complete the prepayment process before confirming the transition. If you encounter issues, see [Services disrupted after canceling a **Prepay** setup](https://docs.cloud.google.com/billing/docs/in-product-billing-setup#prepay-issue).

If you are eligible and manually switch from a **Prepay** cycle to a **Postpay** cycle, any remaining prepay credit balance is automatically refunded to the original payment method used for the prepayment. However, if you close your Cloud Billing account for any other reason, any remaining prepay credits are forfeited and aren't refunded.

#### Buy credits

You can manually purchase credits in advance of your Gemini API usage to load them into your Prepay account credit balance.

To purchase credits, go to the [AI Studio Billing](https://aistudio.google.com/billing) page and select **Buy credits**. The minimum purchase is $5. The maximum amount of credits you can prepay for is $5,000.

#### Auto reload

Auto-reload is an optional feature that automatically tops up your Prepay credit balance when it's running low. This is useful to prevent service interruptions.

You can set up auto reload and see your auto-reload status in the *Available credits* card on the [AI Studio Billing](https://aistudio.google.com/billing) page. Click **Setup auto-reload** or **Manage auto-reload** to set your payment method, reload amount, and the minimum balance that triggers a reload payment.

#### Monthly auto-charge limit

The monthly auto-charge limit is available to Prepay users and helps prevent unexpected costs from frequent automatic credit reloads. Use this feature to set a maximum limit for automatic credit reloads within a single billing cycle. Once the total amount of automatic reloads in a billing cycle reaches this limit, the system disables auto-reload until the start of the next month. One-time payments you initiate manually don't count against this limit.

To set the monthly auto-charge limit when auto-reload is enabled:

1. Go to the [AI Studio Billing](https://aistudio.google.com/billing) page.
2. Click **Manage auto-reload**.
3. Expand the **Monthly Limit** section and enter the maximum monthly limit for auto-reloads.
4. Click **Save**.

### Postpay

In the Postpay billing plan, your Cloud Billing account accrues costs and you are automatically charged at the end of the month, or when your costs reach an automatically assigned spend cap based on your account tier. The payment is charged to the payment method attached to your Postpay payments account, which you can manage on the [AI Studio Billing](https://aistudio.google.com/billing) page. On the **Billing** page you'll be able to view your balance, due dates, and past payments, as well as make payments and manage payment methods.

When setting up billing for a new project, if you are eligible for Postpay, you will have the option to choose between Prepay and Postpay in the billing setup dialogue.

After you switch a Cloud Billing account to use the Postpay billing plan, all projects linked to that billing account are switched to the Postpay plan. You can move an eligible account to Prepay by following the steps in Migrate to prepay. You can also move a project to a billing account with a different billing plan to change the charging cycle for that project; visit the Cloud documentation on [managing billing for projects](https://docs.cloud.google.com/billing/docs/how-to/modify-project).

You can learn more about the Postpay charging cycle in the [Cloud Billing guide](https://docs.cloud.google.com/billing/docs/how-to/billing-cycle).

### Migrate to prepay

Google AI Studio is transitioning developer accounts from Postpay to Prepay billing for Gemini API usage. This change applies only to the Gemini API; other Google Cloud services linked to your billing account remain on Postpay.

Switch to Prepay and add credits before the cutover date in your account notice to avoid service interruptions. Accounts that use only Free Tier features do not need to take action.

To switch an existing Postpay account to Prepay:

1. Go to the [AI Studio Billing](https://aistudio.google.com/billing) page.
2. Select **Switch to Prepay** for your billing account.
3. Purchase credits (minimum $5) to load your starting balance.
To prevent service interruptions after switching, configure auto-reload to top up your credit balance when it runs low.

## Spend caps

The Gemini API supports monthly spend caps at both the billing account tier and project levels. These controls are designed to protect your account from unexpected overages, and the ecosystem to ensure service availability.

*Note that spend caps are not available for [Invoiced (or Offline)](https://docs.cloud.google.com/billing/docs/concepts#billing_account_types) accounts.*

### Project spend caps

You can set your own [project-level](/gemini-api/docs/api-key#google-cloud-projects) spend caps in AI Studio. This is useful if you have multiple projects under the same billing account and want to ensure each has access to enough of the cumulative spending limit.

Accounts with the project editor, owner, or admin [roles](https://docs.cloud.google.com/iam/docs/roles-overview) can set spend caps per project in AI Studio on the [Spend](https://aistudio.google.com/spend) page under **Monthly spend cap** > **Edit spend cap**.

For details on the specific Google Cloud IAM permissions required to view or edit spend caps and billing information in AI Studio, see the [AI Studio troubleshooting guide](/gemini-api/docs/troubleshoot-ai-studio#iam-permissions).

If you [move a project to a different billing account](https://docs.cloud.google.com/billing/docs/how-to/modify-project#change_the_billing_account_for_a_project), any spend cap you already set for that project will persist, but any accumulated spend will reset to $0 for the new billing cycle.

Long-running tasks like [batch mode](/gemini-api/docs/batch-api) completions and agent sessions may incur overages beyond your project spend cap.

Billing data processing times can be delayed in AI Studio, up to around 10 minutes. You may experience overages beyond your project cap if billing data hasn't processed before more charges are accrued.

### Billing account tier spend caps

Each tier has a maximum monthly spend limit:

| Usage tier | Spend cap |
|---|---|
| **Free** | N/A |
| **Tier 1** | $250 |
| **Tier 2** | $2,000 |
| **Tier 3** | $20,000 - $100,000 |
Monthly usage caps are enforced for the Gemini API at the billing account level. While default limits are preset, you can [request an increase](https://docs.google.com/forms/d/e/1FAIpQLSdiP6BWJyNNN65lnwnlOr-5Kv0MOFp0jLQyqi_ixVCfddqWBw/viewform) to accommodate higher usage. Total spend is aggregated across all linked projects that have the Gemini API service enabled. After the cumulative account total reaches the tier limit, service is paused for all projects linked to that billing account until the start of the next billing cycle (the 1st of each month).

#### Evaluate your billing account spend

To evaluate your historical monthly spending to determine if the new Billing Account tier spend caps will impact your ongoing projects, follow these steps:

1. In the Google Cloud console, view your [Cloud Billing account Reports](https://console.cloud.google.com/billing/reports) page.
  - If you have more than one billing account, at the prompt, choose the Cloud Billing account for which you'd like to view cost reports.
2. The report defaults to "Group by Service" in the "Current month". You will see **Gemini API** in the **Service** column and total spend in the **Usage cost** column of the table.
3. To see granular costs limited to Gemini API usage, set the **Group by** filter to group by **SKU**, and the **Services** filter to **Gemini API**.
4. Adjust the **Time range by usage date** filter to your desired range to evaluate your historical spend in a period.

## Processing times

Billing signals and updates don't always happen in real time.

- **Credit usage**: Usage costs are typically drawn down from your balance within minutes.
- **Payment confirmation**: While most card payments are instant, some forms of payment (like bank transfers) may take several days to clear. Services only resume or upgrade after the purchase of credits is officially confirmed.
- **Tier upgrades**: After a successful payment, or when you meet the upgrade criteria, tier upgrades usually reflect within 10 minutes.
- **Total Cost breakdown graphs**: The graphs showing your total cost breakdown on both the [Billing](https://aistudio.google.com/billing) page and the [Spend](https://aistudio.google.com/spend) page can take up to 24 hours to update.
Read the Cloud Billing guides on [charging cycle](https://docs.cloud.google.com/billing/docs/how-to/billing-cycle#delayed-billing) and [transaction](https://docs.cloud.google.com/billing/docs/how-to/view-history#missing-transactions) latencies to learn more about potential billing delays.

## Refunds

Refunds aren't allowed for **Prepay** billing accounts, except when switching account types.

**When a Prepay account switches to the Postpay account type** (after you meet the criteria and manually upgrade your account), the Prepay account is closed and any remaining prepaid credits are automatically refunded to the payment method on file.

If you [close](https://docs.cloud.google.com/billing/docs/how-to/close-or-reopen-billing-account#close-a-billing-account) your Prepay account for any reason other than upgrading to Postpay, any remaining prepaid credits are forfeited.

Purchased credits expire after 1 year. After expiration, credits are forfeited and can't be retrieved.

**Postpay** accounts follow the [Google Cloud refund policy](https://docs.cloud.google.com/billing/docs/how-to/resolve-issues#request_a_refund).

## Cloud Billing accounts

The Gemini API uses [Cloud Billing accounts](https://cloud.google.com/billing/docs/concepts) for billing services, which you can set up directly in AI Studio. You can use AI Studio to track spending, understand costs, and make payments.

Tiers, rate limits, and billing account caps are all determined at the billing account level.

### Projects and API keys

All [projects](/gemini-api/docs/api-key#google-cloud-projects) linked to a Cloud Billing account inherit the billing account's usage tier and associated rate limits and account caps. If you [change a project](https://docs.cloud.google.com/billing/docs/how-to/modify-project#change_the_billing_account_for_a_project) from one billing account to another, its tier, and subsequently rate limits and account caps, will switch to the tier of the new billing account.

Cumulative spend (towards all Google Cloud products) and account age across all projects tied to a billing account counts towards that billing account's tier qualifications.

You can [unlink a project](https://docs.cloud.google.com/billing/docs/how-to/modify-project#disable_billing_for_a_project) from its billing account to return to the free tier.

[API keys](/gemini-api/docs/api-key) are credentials generated inside a project. They have no independent billing settings; they inherit the tier limits and billing status of the project. The cumulative usage from all keys within a project counts toward that project's spend cap and the billing account's total spend.

## Frequently asked questions

The following sections provide answers to frequently asked questions.

Gemini API pricing is based on the following:

- Input token count
- Output token count
- Cached token count
- Cached token storage duration
For pricing information, see the [Pricing page](https://ai.google.dev/pricing).

You can view your quota and system limits in [AI Studio](https://aistudio.google.com/usage).

You will automatically be granted more quota when your account reaches the next [tier requirements](/gemini-api/docs/rate-limits#usage-tiers).

Yes, we make the free tier and paid tier available in [many regions](/gemini-api/docs/available-regions).

AI Studio usage remains free of charge unless users link a paid API key for access to paid features. Once you link a paid API key as part of a paid project in AI Studio, you will be charged for AI Studio usage for that key. You can switch between Paid Tier projects and Free Tier projects as needed by using the respective API keys linked to each type.

To access higher tiers, you must set up billing on your project. Click **Set up billing** in Google AI Studio. This will walk you through selecting or creating a Cloud Billing account. If you are required to be on the prepaid billing model, the **Set up billing** process will guide you through the process to create your Prepay account that is linked to your Cloud Billing account.

The free tier for Gemini API differs based on the model selected. For now, you can try the 1M token context window in the following ways:

- In Google AI Studio
- With free-of-charge plans for select models
- With postpaid plans
To downgrade to the Free Tier, you can [disable billing](https://docs.cloud.google.com/billing/docs/how-to/modify-project#disable_billing_for_a_project) on each of your projects that you want to downgrade.

Use the [`GenerativeModel.count_tokens`](/api/python/google/generativeai/GenerativeModel#count_tokens) method to count the number of tokens. Refer to the [Tokens guide](/gemini-api/docs/tokens) to learn more about tokens.

When you sign up for your first ever Cloud Billing account, your [Google Cloud Free Trial](https://docs.cloud.google.com/free/docs/free-cloud-features#free-trial) starts and you are granted a $300 [Welcome credit](https://docs.cloud.google.com/billing/docs/in-product-billing-setup#welcome-credits). However, those credits can't be used to pay for AI Studio usage. You can use the Welcome credit to pay for other eligible services within Google Cloud (note that once those credits are consumed or expire (within 90 days), any additional usage costs are automatically billed to your established form of payment).

No, the Google Cloud [Welcome credit](https://docs.cloud.google.com/billing/docs/in-product-billing-setup#welcome-credits) or free trial credit can't be used towards the Gemini API or AI Studio.

If you were granted a Google Cloud welcome credit before they became ineligible, you are allowed to spend your remaining credits on the Gemini API and AI Studio up until the credits expire (after 90 days).

No, starting March 2026, Gemini API usage costs are specifically excluded from the [$300 Google Cloud Free Trial](https://docs.cloud.google.com/free/docs/free-cloud-features#free-trial) program.

Prepay users must first purchase Prepaid credits before any eligible Google Cloud credits can be applied to Gemini API usage. Once you have an active Prepay credit balance, Google Cloud credits that are eligible for the Gemini API are consumed before your Prepay credit balance. When your Prepay credit balance on the billing account hits $0, Google Cloud credits will no longer be consumed.

Not all Google Cloud credits, such as the Google Cloud Welcome credit, can be used towards Gemini API and AI Studio.

Billing for the Gemini API is handled by the [Cloud billing](https://cloud.google.com/billing/docs/concepts) system. Learn about the in-product Cloud Billing setup in the [Cloud Billing documentation](https://docs.cloud.google.com/billing/docs/in-product-billing-setup).

If your request fails with a 400 or 500 error, you won't be charged for the tokens used. However, the request will still count against your quota.

Requests to the `GetTokens` API are not billed, and they don't count against inference quota.

Refer to the [Terms of service](/gemini-api/terms#paid-services) for details on how data is handled when Cloud billing is enabled (see "How Google Uses Your Data" under "Paid Services"). Note that your Google AI Studio prompts are treated under the same "Paid Services" terms so long as at least 1 API project has billing enabled, which you can validate on the [Gemini API key page](https://aistudio.google.com/api-keys) if you see any projects marked as "Paid" under "Plan".

Prepaid billing allows users of Gemini API in AI Studio to pre-purchase credits. Starting Mar 23, 2026, new users to AI Studio might be required to be on the Prepaid billing plan. During the AI Studio Set up Billing process, the UI will guide you through the billing set up flow and will indicate if you are required to prepay.

You can purchase credits on the AI Studio Billing page. During the purchase process, the UI will provide the minimum pre-purchase amount that is required for your region and tier level, as well as a maximum amount that can be in your account at one time.

Yes, we recommend that you configure auto-reload in the AI Studio Billing settings. You specify a "trigger" credit balance (e.g., "when my balance falls below $30") and a "reload value" (e.g., "add $100").

Yes, Prepay users can set a Monthly Auto-Charge Limit within the **Auto-Reload** widget. When the total amount of automatic reloads in a billing cycle reaches this limit, the system disables auto-reload until the next month. Manual credit purchases do not count toward this limit.

All Prepaid API credits expire after 1 year and cannot be refunded. Read the refund policy for Prepay accounts.

Yes, credits expire 12 months after their purchase date.

All Gemini API services in all projects paid for by that Cloud Billing Prepay account will stop immediately to prevent incurring more charges. Your projects aren't automatically downgraded to the Free Tier.

To restore service at your current Paid Tier level, you must purchase additional credits. After you've purchased credits, you should be able to use the Gemini API. Note that there might be a delay while our systems update to reflect your credit balance.

Optionally, to downgrade to the Free Tier, you can [disable billing](https://docs.cloud.google.com/billing/docs/how-to/modify-project#disable_billing_for_a_project) on the projects you want to downgrade.

You may have hit the usage limit for your current tier. Usage limits will increase automatically as you progress to higher tiers. Your Gemini API AI Studio usage can also be impacted due to the status of your Cloud Billing account.

Due to the complexity of our billing and processing systems, there might be delays in our ability to cut off usage after you consume all of your credits. This excess usage might appear as a negative credit balance in your AI Studio billing dashboard. If this happens, your service is paused, and your negative balance will be deducted from your next credit purchase.

To avoid a pause in your Gemini API service, we recommend setting up auto-reload to automatically purchase more credits when your credit balance falls below a value you specify.

No, Prepay credits are strictly locked to Gemini API usage. Any other Google Cloud services you use (Compute, Storage, Gemini Enterprise Agent Platform) are billed using the standard [Cloud charging cycle](https://docs.cloud.google.com/billing/docs/how-to/billing-cycle).

No, switching from a Prepay billing plan to a Postpay billing plan is not supported.

Yes, you can transition an existing Postpay account on the [AI Studio Billing](https://aistudio.google.com/billing) page. See Migrate to prepay for instructions.

When you upgrade to Postpay, Cloud Billing closes your Prepay payments account, turns off auto-reload, and automatically refunds any unused Prepay credits to you (subject to standard refund processing time).

All balance management and transaction history for the Gemini API must be done directly within the Google AI Studio Billing tab.

Payments interactions on the [AI Studio Billing page](https://aistudio.google.com/billing) may be blocked and replaced with the message "The billing account type is inactive or unsupported" if your selected billing account type or billing account status is not eligible for the Paid Tier in AI Studio.

Check the [Cloud Console](https://console.cloud.google.com/billing/) to see your billing account's status. One ineligible type could be *Free trial account*, in which case you can activate billing in AI Studio to become eligible. One inactive state could be *Closed*, in which case you can [reopen the account](https://docs.cloud.google.com/billing/docs/how-to/close-or-reopen-billing-account).

Yes, Gemini API costs, alongside costs associated with any other Google Cloud services that are paid for by your Cloud Billing account, are viewable on the [Cost management pages](https://docs.cloud.google.com/billing/docs/how-to/split-charging-cycle#cost-reports) in the [Cloud Billing console](https://console.cloud.google.com/billing). Note that you can only manage your Prepay credit balance in AI Studio.

Google Cloud and AI Studio report usage data to Cloud Billing at varying intervals. Due to the complexity of our billing and processing systems, you might see a delay between your use of services, and the usage and costs being available to view in Cloud Billing. Typically, your cost details are available within a day, but can sometimes take more than 24 hours. Learn more about delayed billing in the [Cloud Billing documentation](https://docs.cloud.google.com/billing/docs/how-to/billing-cycle#delayed-billing).

Missing a payment for other Google Cloud services can suspend your Gemini API access in AI Studio, **regardless of how many Prepaid credits you have available**. AI Studio usage is powered by a Google Cloud Billing account, which can share both Prepay billing for AI Studio and Postpay billing for other Cloud services. An issue with your Postpay balance halts all services tied to that account. Your Gemini API usage will be suspended if your Cloud Billing account is flagged for issues such as:

- A delinquent or overdue balance
- A declined payment
- An invalid or expired payment method
To restore service, you must [resolve the Postpay account issue](https://docs.cloud.google.com/billing/docs/how-to/resolve-issues#resolving-declined-payments) in the Google Cloud Billing console. Once you resolve the issue, you will regain access to your Prepaid Gemini API credits and services.

**Issue:** You started the flow to add Prepay capabilities to an existing Postpay billing account, but closed the window or canceled the process before completing the prepayment setup. Other projects linked to that billing account lost access to the Gemini API.

**Cause:** During the transition flow, the infrastructure to support Prepay is created on your billing account immediately after you accept the confirmation dialog. If you don't complete the prepayment steps, the configuration remains in an unchargeable state. Because this state applies at the billing account level, it restricts access for all projects linked to that billing account that rely on Prepay services.

**Resolution:** Because the account state has already changed, there is no automatic way to revert the state if you abandon the payment flow. To restore service to your linked projects, do one of the following:

- **Complete the setup:** Return to Google AI Studio, restart the billing setup flow, and complete the prepayment process. After the payment is processed, the Prepay billing plan becomes active and the service is restored.
- **Contact Support:** If you don't want to use the Prepay billing plan and want to revert your billing account back to Postpay, [contact Cloud Billing Support](https://cloud.google.com/support/billing) to manually reset your account state.
To get help with billing, see [Get Cloud billing support](https://cloud.google.com/support/billing).

Except as otherwise noted, the content of this page is licensed under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/), and code samples are licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0). For details, see the [Google Developers Site Policies](https://developers.google.com/site-policies). Java is a registered trademark of Oracle and/or its affiliates.

Last updated 2026-09-28 UTC.