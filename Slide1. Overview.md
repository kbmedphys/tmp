## Slide1. Overview

"Let me start with some background.  
Our focus is on identifying regimes of shifting inflation using the Consumer Price Index, or CPI. Now, as you know, CPI is only released once a month. Because of this infrequent schedule — and the publication lag — it has serious limitations when it comes to capturing what’s happening in the economy in real time.

So, we apply *nowcasting regimes*. There’s actually a large amount of information that influences monthly or even quarterly inflation readings, but it’s available at much higher frequencies — daily or weekly. By leveraging this high-frequency data, we can generate what’s called a ‘nowcast.’ Essentially, it’s a timely estimate for series that are otherwise published only at lower frequencies. And using this nowcasted data, we can estimate inflation regimes much more effectively, giving us a clearer, real-time picture of inflation dynamics."

## Slide2. MF-Methods used for Nowcasting

"Before the CPI is released, we already have a variety of higher-frequency indicators — for example, daily oil prices or raw commodity prices. These contain predictive information about CPI inflation and can be extremely useful in producing a timely nowcast.

To integrate these signals, we use what’s called a *Mixed-Frequency Dynamic Factor Model*, or MF-DFM. This framework combines both high-frequency and low-frequency indicators into one coherent structure.

The logic of a Dynamic Factor Model is simple but powerful: a large number of observed variables tend to move together over the business cycle, and this co-movement can be explained by just a few latent, unobserved factors. These hidden factors capture the common dynamics driving the system. Rather than modeling every variable separately, we summarize the variation in terms of these underlying factors."

## Slide3. Procedure

"To capture changes in CPI as early as possible, we use commodity futures prices as more timely data. The assumption is that both the monthly CPI and the daily futures prices share a common latent inflation component.

For example, the figure here shows the year-on-year change rates of the energy index in CPI alongside crude oil and natural gas. You can clearly see that these high-frequency series contain valuable information about inflation dynamics.

The process works in three steps:

1. Model latent inflation factors using both monthly and high-frequency data.

2. Estimate CPI contributions on a *weekly basis* using the mixed-frequency dynamic model.

3. Finally, estimate inflation regimes from those weekly CPI contributions.

This allows us to bridge the gap between official monthly releases and market-driven daily signals."

## Slide4. The Data Flow and Nowcasting Model

"We then estimate a dynamic factor model on a large panel of daily futures data, along with the monthly CPI. Each time new futures data arrives, the model’s nowcast updates, giving us a continuously refreshed estimate.

On the slide, the **left panel** shows the four target monthly CPI contributions: Services, Commodities, Food, and Energy. The **right panel** lists the futures series we use as high-frequency predictors, assumed to be closely related to these contributions.

This setup links the slow-moving CPI with fast-moving futures data, producing an evolving nowcast that improves as new information flows in."

## Slide5. MF-DFM

"Dynamic Factor Models, or DFMs, are based on a core principle: that many economic variables move together over the business cycle and can be explained by a much smaller set of latent factors.

Formally, the observed variables, *y*, are driven by these hidden dynamic factors, *f*, which are typically modeled as autoregressive processes to capture persistence.

Extending this idea to mixed-frequency data, we estimate latent factors weekly and then generate nowcasts for the monthly series. This way, we bridge weekly and monthly data into a single framework. By applying an aggregation function, high-frequency factors can be aligned with low-frequency targets. In partially observed periods, the missing portion is estimated through a state-space model with Kalman filtering.

Using the estimated weekly latent factors *f*, we can generate nowcasts for those series that are published only at the monthly frequency."

## Slide6. Nowcasting CPI Contributions on a Weekly Basis

**CPI Components: Services, Commodities, Food, Energy**  
"When we apply this framework, we focus on four CPI components: Services, Commodities, Food, and Energy. Futures data are used to nowcast each of these components.

In the figure, scatter points represent the observed data, while the solid line shows the model estimates. As you can see, the weekly nowcasts align well with the observations, demonstrating the effectiveness of this approach."

This demonstrates that the mixed-frequency framework, when combined with futures data, is able to capture short-term movements in CPI components effectively, providing a reliable and timely signal of inflationary trends."

## Slide7. Regime Identification Model

"Now, to identify regimes, we use a *Statistical Jump Model*. This is an unsupervised algorithm designed to cluster temporal features while also penalizing excessive state changes.

If the penalty parameter, lambda, is set to zero, the method reduces to standard K-means, which ignores time ordering. But as we increase lambda, the number of regime switches decreases, producing smoother transitions.

The objective function has two terms: the first is the usual K-means loss, and the second is the jump penalty. By adjusting lambda, we balance between flexibility and stability."

## Slide8. Nowcasting Inflation Regimes

"Time-series clustering allows us to adapt to changing dynamics in financial markets. The critical step is tuning lambda carefully, either through cross-validation or statistical criteria.

In our results, we fixed lambda at 10. The **upper panel** shows monthly inflation regimes, while the **lower panel** shows weekly nowcasts. The colors represent regime probabilities. The takeaway is that by incorporating high-frequency data, we can detect regime shifts more quickly than relying on monthly CPI alone."

## Slide9. Statistical Jump Models, using different jump penalty values 0,10,100

"We also tested robustness by changing lambda across values of zero, ten, and one hundred. Interestingly, in this dataset, the results did not change significantly. This suggests the identified regimes are relatively stable, regardless of hyperparameter choice."

## Slide10. Limitation

"That said, there are limitations. When estimating regimes on a daily basis, noise becomes a problem. Modeling monthly data at daily frequency means parameter estimates can reflect short-term fluctuations, not just the underlying signal.

The figure illustrates this: the **left panel** shows daily estimation, which is noisy, while the **right panel** shows weekly estimation, which is much more stable. Weekly frequency strikes a good balance between timeliness and reliability."

## Slide11. Nowcasting Macroeconomic Regimes

"Next, we extend this method to nowcasting *macroeconomic regimes*. We use ten monthly variables — the U.S. Leading Economic Index indicators — along with eight weekly variables from the FRED dataset.

By combining these, we estimate latent factors in real time and nowcast macroeconomic regimes, providing timely insights into the broader economic cycle."

## Slide12. Nowcasting Macroeconomic Regimes with a fixed jump penalty of 20.

"Here, we fix lambda at 20 and estimate regimes on a weekly frequency.

The identified regimes generally track well, but we observe some latency at the start and end of market crashes. During prolonged turbulence, sharp oscillations can sometimes be misinterpreted as regime shifts.

One possible improvement would be to add more descriptive features — either to detect trends and oscillations in return series, or to reflect broader macroeconomic conditions. This would make the Statistical Jump Model more robust."

## Slide13. Online Nowcasting

"We also explored an online nowcasting framework. Here, the model was estimated at the beginning of 2020, and then updated with new data as it arrived — without re-estimating parameters.

Even if regime boundaries don’t move, the temporal order of new data can still lead to regimes being reassigned. In other words, past regimes may be retroactively adjusted to minimize the total loss function.

This online approach provides a continuously updated view of regimes, aligned with new information as it comes in."

## Slide14. Summary

"To summarize:

**Contributions:**

- We nowcast CPI and the Leading Economic Index on a *weekly basis* using a mixed-frequency dynamic factor model.

- These weekly estimates enable us to identify inflation and macroeconomic regimes at a much higher frequency.

**Limitations:**

- Regimes can be retroactively adjusted, since they depend on the temporal ordering of data.

- In macroeconomic regime estimation, results can vary with the jump penalty parameter. This makes careful tuning — via cross-validation or statistical criteria — essential."

**Future Work**  
"Looking ahead, an important next step is to evaluate the **short-term forecasting accuracy** of regime identification when incorporating high-frequency data.

This will help us move from retrospective regime detection toward practical forecasting tools that can directly inform portfolio management and risk control."
