export type Profile = {
  display_name: string | null;
  username: string | null;
  bio: string | null;
  account_created_at: string;
  avatar_url: string | null;
  community_unit: { name: string; kind: "branch" | "ward" | "stake" } | null;
};

export type ProfileUpdate = {
  display_name?: string | null;
  username?: string | null;
  bio?: string | null;
};
