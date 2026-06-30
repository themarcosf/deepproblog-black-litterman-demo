%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Neural predicate
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

nn(classifier,
   [Company],
   Stance,
   [bullish, bearish, neutral]) ::
market_stance(Company, Stance).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Rules
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

bullish_company(Company) :-
    market_stance(Company, bullish).

bearish_company(Company) :-
    market_stance(Company, bearish).

neutral_company(Company) :-
    market_stance(Company, neutral).