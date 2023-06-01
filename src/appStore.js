import create from 'zustand'
import {devtools, persist} from 'zustand/middleware'

let store = (set) => ({
    people: ['gabriel', 'simon', 'sean'],
    addPerson: (person) =>
        set((state) => ({ people: [...state.people, person]})),
    
    week: 4,
    setWeek: (newData) => set((state) => ({ week: newData })),

    speed: 100,
    setSpeed: (newData) => set((state) => ({ speed: newData })),

})

store = devtools(store)
//store = persist(store, {name: 'user_settings'})  


const useStore = create(store)

export default useStore