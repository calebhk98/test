import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';
import { DiscoveryGridScreen } from '../screens/discovery/DiscoveryGridScreen';
import { ProfileViewScreen } from '../screens/discovery/ProfileViewScreen';
import { MatchesListScreen } from '../screens/matches/MatchesListScreen';
import { ConversationScreen } from '../screens/matches/ConversationScreen';
import { ProposeDateScreen } from '../screens/matches/ProposeDateScreen';
import { DateProposalDetailScreen } from '../screens/matches/DateProposalDetailScreen';
import { CheckInScreen } from '../screens/matches/CheckInScreen';
import { QuestionFlowScreen } from '../screens/questions/QuestionFlowScreen';
import { MoreMenuScreen } from '../screens/more/MoreMenuScreen';
import { WalletScreen } from '../screens/more/WalletScreen';
import { TicketDetailScreen } from '../screens/more/TicketDetailScreen';
import { StatsScreen } from '../screens/more/StatsScreen';
import { TrustScreen } from '../screens/more/TrustScreen';
import { SettingsScreen } from '../screens/more/SettingsScreen';
import { colors } from '../theme/tokens';
import type {
  DiscoveryStackParamList,
  MainTabParamList,
  MatchesStackParamList,
  MoreStackParamList,
  QuestionsStackParamList,
} from './types';

const DiscoveryStack = createNativeStackNavigator<DiscoveryStackParamList>();
const MatchesStack = createNativeStackNavigator<MatchesStackParamList>();
const QuestionsStack = createNativeStackNavigator<QuestionsStackParamList>();
const MoreStack = createNativeStackNavigator<MoreStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

function DiscoveryStackNavigator(): React.ReactElement {
  return (
    <DiscoveryStack.Navigator>
      <DiscoveryStack.Screen name="DiscoveryGrid" component={DiscoveryGridScreen} options={{ headerShown: false }} />
      <DiscoveryStack.Screen name="ProfileView" component={ProfileViewScreen} options={{ title: 'Profile' }} />
    </DiscoveryStack.Navigator>
  );
}

function MatchesStackNavigator(): React.ReactElement {
  return (
    <MatchesStack.Navigator>
      <MatchesStack.Screen name="MatchesList" component={MatchesListScreen} options={{ headerShown: false }} />
      <MatchesStack.Screen name="Conversation" component={ConversationScreen} options={{ title: 'Conversation' }} />
      <MatchesStack.Screen name="ProposeDate" component={ProposeDateScreen} options={{ title: 'Propose a date' }} />
      <MatchesStack.Screen name="DateProposalDetail" component={DateProposalDetailScreen} options={{ title: 'Date' }} />
      <MatchesStack.Screen name="CheckIn" component={CheckInScreen} options={{ title: 'Check in' }} />
    </MatchesStack.Navigator>
  );
}

function QuestionsStackNavigator(): React.ReactElement {
  return (
    <QuestionsStack.Navigator>
      <QuestionsStack.Screen name="QuestionFlow" component={QuestionFlowScreen} options={{ title: 'Questions' }} />
    </QuestionsStack.Navigator>
  );
}

function MoreStackNavigator(): React.ReactElement {
  return (
    <MoreStack.Navigator>
      <MoreStack.Screen name="MoreMenu" component={MoreMenuScreen} options={{ headerShown: false }} />
      <MoreStack.Screen name="Wallet" component={WalletScreen} options={{ headerShown: false }} />
      <MoreStack.Screen name="TicketDetail" component={TicketDetailScreen} options={{ title: 'Ticket' }} />
      <MoreStack.Screen name="Stats" component={StatsScreen} options={{ headerShown: false }} />
      <MoreStack.Screen name="Trust" component={TrustScreen} options={{ headerShown: false }} />
      <MoreStack.Screen name="Settings" component={SettingsScreen} options={{ headerShown: false }} />
    </MoreStack.Navigator>
  );
}

function tabIcon(glyph: string) {
  return function TabIcon({ color }: { color: string }): React.ReactElement {
    return <Text style={{ fontSize: 20, color }}>{glyph}</Text>;
  };
}

export function MainNavigator(): React.ReactElement {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.textSecondary,
      }}
    >
      <Tab.Screen
        name="DiscoveryTab"
        component={DiscoveryStackNavigator}
        options={{ title: 'Discover', tabBarIcon: tabIcon('◎'), tabBarLabel: 'Discover' }}
      />
      <Tab.Screen
        name="QuestionsTab"
        component={QuestionsStackNavigator}
        options={{ title: 'Questions', tabBarIcon: tabIcon('?'), tabBarLabel: 'Questions' }}
      />
      <Tab.Screen
        name="MatchesTab"
        component={MatchesStackNavigator}
        options={{ title: 'Matches', tabBarIcon: tabIcon('♥'), tabBarLabel: 'Matches' }}
      />
      <Tab.Screen
        name="MoreTab"
        component={MoreStackNavigator}
        options={{ title: 'More', tabBarIcon: tabIcon('•••'), tabBarLabel: 'More' }}
      />
    </Tab.Navigator>
  );
}
