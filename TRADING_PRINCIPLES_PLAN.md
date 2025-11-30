# Trading Principles Feature Implementation Plan

## Overview
Add a "원칙(Principles)" button to the header that opens a modal for managing trading principles. Users can add, view, and save multiple trading principles that are stored in a new `principles` database table.

## Architecture

### 1. Database Layer
**New Table: `principles`**
```sql
CREATE TABLE principles (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    principle_text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);
```

**Model: `Principle` (back/app/models.py)**
- `id`: Primary key
- `user_id`: Foreign key to users table
- `principle_text`: The principle content (text)
- `created_at`, `updated_at`: Timestamps

### 2. Backend API Layer
**New Router: `back/app/routers/principles.py`**

Endpoints:
- `GET /api/principles/` - Get all principles for current user
- `POST /api/principles/` - Create new principle(s)
- `DELETE /api/principles/{principle_id}` - Delete a principle

Pattern: Follow trading_plans.py conventions
- Use `Depends(get_current_user)` for authentication
- Filter by `user_id == current_user.id`
- Return paginated responses

### 3. Frontend Components
**New Modal: `front/src/components/principles-modal.tsx`**

Features:
- Modal dialog with title and close button
- Text input field for entering a new principle
- "추가" (Add) button to add principle to list
- List of current principles with delete buttons for each
- Footer with "확인" (Confirm) and "취소" (Cancel) buttons
- Use react-query for fetching/mutating principles
- Loading and error states

**Header Button: Update `front/src/components/header.tsx`**
- Add "원칙" button with icon (e.g., BookOpen or Lightbulb)
- Pass `onPrincipleManage` callback
- Add to both desktop and mobile views

**Dashboard Integration: Update `front/src/app/dashboard/page.tsx`**
- Add state for principles modal visibility
- Pass callbacks to Header component
- Render PrinciplesModal component

### 4. Frontend API Module
**Update: `front/src/lib/api.ts`**

Add principlesAPI object:
```typescript
export const principlesAPI = {
  getPrinciples: () => api.get('/api/principles/'),
  createPrinciple: (principle_text: string) =>
    api.post('/api/principles/', { principle_text }),
  deletePrinciple: (principleId: number) =>
    api.delete(`/api/principles/${principleId}`),
}
```

## Implementation Steps

### Phase 1: Backend (Database & API)
1. Add Principle model to models.py
2. Create principles router (back/app/routers/principles.py)
3. Register router in main.py
4. Test endpoints with Postman/curl

### Phase 2: Frontend Components
1. Create principles-modal.tsx component
2. Update header.tsx to add "원칙" button
3. Update dashboard/page.tsx to manage modal state
4. Update api.ts with principlesAPI functions

### Phase 3: Integration & Testing
1. Test adding principles
2. Test listing principles
3. Test deleting principles
4. Test persistence to database
5. Build and deploy frontend

## UI Design

### Principles Modal Layout
```
┌─────────────────────────────────────┐
│ 매매원칙                  [X]        │
├─────────────────────────────────────┤
│                                     │
│ [입력칸을 넣어줘]                   │
│ [추가]                              │
│                                     │
│ • 원칙 1 [삭제]                     │
│ • 원칙 2 [삭제]                     │
│ • 원칙 3 [삭제]                     │
│                                     │
├─────────────────────────────────────┤
│           [확인]  [취소]            │
└─────────────────────────────────────┘
```

## Key Design Decisions

1. **Simple List Management**: No edit function, only add/delete
2. **Immediate Add**: Principles added to list immediately without server save
3. **Batch Save**: All changes saved on "확인" click
4. **User Isolation**: Each user has own principles via user_id FK
5. **No Ordering**: Principles display in insertion order (created_at)

## Dependencies
- Backend: SQLAlchemy ORM already available
- Frontend: react-query already available
- UI: Tailwind CSS already available

## Testing Checklist
- [ ] Database table created with proper constraints
- [ ] Backend endpoints respond correctly
- [ ] Frontend modal opens/closes
- [ ] Can add principles via input + button
- [ ] Can delete principles from list
- [ ] Can save all principles with confirm button
- [ ] Principles persist after page reload
- [ ] User A's principles don't appear for User B
- [ ] Mobile and desktop views both work
