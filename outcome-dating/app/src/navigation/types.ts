/** Navigation param lists, one place, so a screen's required params are a type error away from being wrong at any call site. */

export type AuthStackParamList = {
  Welcome: undefined;
  SignUp: undefined;
  Login: undefined;
};

export type DiscoveryStackParamList = {
  DiscoveryGrid: undefined;
  ProfileView: { userId: string };
};

export type MatchesStackParamList = {
  MatchesList: undefined;
  Conversation: { conversationId: string; displayName: string };
  ProposeDate: { conversationId: string; recipientDisplayName: string };
  DateProposalDetail: { dateProposalId: string };
  CheckIn: { dateProposalId: string };
};

export type QuestionsStackParamList = {
  QuestionFlow: undefined;
};

export type MoreStackParamList = {
  MoreMenu: undefined;
  Wallet: undefined;
  TicketDetail: { ticketId: string };
  Stats: undefined;
  Trust: undefined;
  Settings: undefined;
};

export type MainTabParamList = {
  DiscoveryTab: undefined;
  MatchesTab: undefined;
  QuestionsTab: undefined;
  MoreTab: undefined;
};
