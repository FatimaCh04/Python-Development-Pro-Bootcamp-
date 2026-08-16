export const trendingTags = [
  { tag: '#reactjs', posts: 2140 },
  { tag: '#buildinpublic', posts: 1876 },
  { tag: '#flaskapi', posts: 942 },
  { tag: '#uiux', posts: 811 },
  { tag: '#opensource', posts: 604 },
  { tag: '#postgresql', posts: 388 },
]

export const initialPosts = [
  {
    id: 'p1',
    author: { name: 'Sara Khan', handle: '@sarak', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=sarak' },
    content: "Finally shipped the redesign for our internal tools. Clean data in, clean UI out. #uiux #buildinpublic",
    image: 'https://images.unsplash.com/photo-1522199755839-a2bacb67c546?w=900&q=80',
    timestamp: '2h ago',
    likes: 128,
    liked: false,
    tags: ['#uiux', '#buildinpublic'],
    comments: [
      {
        id: 'c1',
        author: { name: 'Umar Iqbal', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=umar' },
        content: 'This is so clean, love the contrast choices.',
        timestamp: '1h ago',
        replies: [
          {
            id: 'c1r1',
            author: { name: 'Sara Khan', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=sarak' },
            content: 'Thank you! Took a few passes to get right.',
            timestamp: '45m ago',
            replies: [],
          },
        ],
      },
    ],
  },
  {
    id: 'p2',
    author: { name: 'Ali Raza', handle: '@alidev', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=alidev' },
    content: 'Migrated our post storage to PostgreSQL with proper indexing on hashtags. Query time down 8x. #postgresql #flaskapi',
    image: null,
    timestamp: '4h ago',
    likes: 76,
    liked: true,
    tags: ['#postgresql', '#flaskapi'],
    comments: [],
  },
  {
    id: 'p3',
    author: { name: 'Meher Fatima', handle: '@meherf', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=meherf' },
    content: 'Open sourced our JWT auth boilerplate for Flask + React. Link in bio. #opensource #reactjs',
    image: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=900&q=80',
    timestamp: '6h ago',
    likes: 342,
    liked: false,
    tags: ['#opensource', '#reactjs'],
    comments: [
      {
        id: 'c2',
        author: { name: 'Sara Khan', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=sarak' },
        content: 'Been waiting for something like this, thank you!',
        timestamp: '5h ago',
        replies: [],
      },
    ],
  },
]
